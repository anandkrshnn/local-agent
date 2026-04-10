"""
Load Balancer for Multiple Ollama Instances
Distributes requests across instances for higher throughput
"""

import asyncio
import random
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED = "weighted"

@dataclass
class InstanceInfo:
    """Information about an Ollama instance"""
    url: str
    weight: int = 1
    active_connections: int = 0
    last_latency: float = 0
    health_status: bool = True
    last_health_check: float = 0

class OllamaLoadBalancer:
    """
    Load balancer for multiple Ollama instances
    Supports multiple strategies and health checking
    """
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self.instances: List[InstanceInfo] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
        self.health_check_interval = 30  # seconds
    
    def add_instance(self, url: str, weight: int = 1):
        """Add an Ollama instance to the pool"""
        self.instances.append(InstanceInfo(url=url, weight=weight))
    
    def remove_instance(self, url: str):
        """Remove an instance from the pool"""
        self.instances = [i for i in self.instances if i.url != url]
    
    async def _check_health(self, instance: InstanceInfo) -> bool:
        """Check if an instance is healthy"""
        import requests
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{instance.url}/api/tags",
                timeout=5
            )
            is_healthy = response.status_code == 200
            if is_healthy:
                instance.last_latency = response.elapsed.total_seconds() * 1000
            instance.health_status = is_healthy
            instance.last_health_check = time.time()
            return is_healthy
        except:
            instance.health_status = False
            return False
    
    async def _health_check_all(self):
        """Check health of all instances"""
        tasks = [self._check_health(instance) for instance in self.instances]
        await asyncio.gather(*tasks)
    
    async def _get_best_instance_round_robin(self) -> Optional[InstanceInfo]:
        """Round-robin selection"""
        if not self.instances:
            return None
        
        for _ in range(len(self.instances)):
            instance = self.instances[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.instances)
            if instance.health_status:
                return instance
        
        return None
    
    async def _get_best_instance_least_connections(self) -> Optional[InstanceInfo]:
        """Select instance with fewest active connections"""
        healthy = [i for i in self.instances if i.health_status]
        if not healthy:
            return None
        
        return min(healthy, key=lambda i: i.active_connections)
    
    async def _get_best_instance_random(self) -> Optional[InstanceInfo]:
        """Random selection"""
        healthy = [i for i in self.instances if i.health_status]
        if not healthy:
            return None
        
        return random.choice(healthy)
    
    async def _get_best_instance_weighted(self) -> Optional[InstanceInfo]:
        """Weighted random selection based on weight and latency"""
        healthy = [i for i in self.instances if i.health_status]
        if not healthy:
            return None
        
        # Calculate weights (lower latency = higher weight)
        weights = []
        for i in healthy:
            if i.last_latency > 0:
                weight = i.weight * (1000 / max(i.last_latency, 1))
            else:
                weight = i.weight
            weights.append(weight)
        
        total = sum(weights)
        if total == 0:
            return healthy[0]
        
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return healthy[i]
        
        return healthy[0]
    
    async def get_instance(self) -> Optional[InstanceInfo]:
        """Get the best instance based on strategy"""
        # Periodic health check
        if time.time() % self.health_check_interval < 1:
            asyncio.create_task(self._health_check_all())
        
        async with self._lock:
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return await self._get_best_instance_round_robin()
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return await self._get_best_instance_least_connections()
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return await self._get_best_instance_random()
            elif self.strategy == LoadBalancingStrategy.WEIGHTED:
                return await self._get_best_instance_weighted()
            
            return await self._get_best_instance_least_connections()
    
    async def execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute a request on the best available instance"""
        instance = await self.get_instance()
        if not instance:
            raise Exception("No healthy Ollama instances available")
        
        instance.active_connections += 1
        start_time = time.time()
        
        try:
            import requests
            response = await asyncio.to_thread(
                requests.post,
                f"{instance.url}/api/generate",
                json={
                    "model": kwargs.get('model', 'phi3:mini'), 
                    "prompt": prompt, 
                    "stream": False,
                    "options": kwargs.get('options', {})
                },
                timeout=kwargs.get('timeout', 60)
            )
            
            latency = (time.time() - start_time) * 1000
            instance.last_latency = latency
            
            return {
                "success": True,
                "response": response.json().get('response', ''),
                "instance": instance.url,
                "latency_ms": latency
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "instance": instance.url
            }
        finally:
            instance.active_connections -= 1
    
    def get_stats(self) -> Dict:
        """Get load balancer statistics"""
        return {
            "strategy": self.strategy.value,
            "total_instances": len(self.instances),
            "healthy_instances": sum(1 for i in self.instances if i.health_status),
            "instances": [
                {
                    "url": i.url,
                    "weight": i.weight,
                    "active_connections": i.active_connections,
                    "last_latency_ms": i.last_latency,
                    "healthy": i.health_status
                }
                for i in self.instances
            ]
        }

# Singleton instance
load_balancer = OllamaLoadBalancer(strategy=LoadBalancingStrategy.LEAST_CONNECTIONS)
