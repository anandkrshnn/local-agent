"""Ollama provider for local models"""

import requests
import time
from typing import List
from .base import ModelProvider, ModelResponse, ModelTier

class OllamaProvider(ModelProvider):
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "phi3:mini"):
        self.endpoint = endpoint
        self.model = model
        self._available = None
    
    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            resp = requests.get(f"{self.endpoint}/api/tags", timeout=2)
            self._available = resp.status_code == 200
            return self._available
        except:
            self._available = False
            return False
    
    def get_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return [m['name'] for m in resp.json().get('models', [])]
        except:
            return []
    
    def get_tier(self) -> ModelTier:
        # Determine tier based on model size
        if "tiny" in self.model.lower():
            return ModelTier.TINY
        elif "7b" in self.model.lower() or "8b" in self.model.lower():
            return ModelTier.MEDIUM
        elif "3b" in self.model.lower() or "mini" in self.model.lower():
            return ModelTier.SMALL
        else:
            return ModelTier.MEDIUM
    
    def get_estimated_latency_ms(self) -> float:
        # Ollama local inference
        if self.get_tier() == ModelTier.TINY:
            return 200
        elif self.get_tier() == ModelTier.SMALL:
            return 500
        else:
            return 1500
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start = time.time()
        
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.7),
                    "num_predict": kwargs.get('max_tokens', 512)
                }
            },
            timeout=kwargs.get('timeout', 120)
        )
        
        elapsed = time.time() - start
        result = response.json()
        
        return ModelResponse(
            content=result.get('response', ''),
            provider="Ollama",
            model=self.model,
            tier=self.get_tier(),
            latency_ms=elapsed * 1000,
            tokens_per_second=result.get('eval_count', 0) / elapsed if elapsed > 0 else 0,
            input_tokens=result.get('prompt_eval_count', 0),
            output_tokens=result.get('eval_count', 0)
        )

    async def generate_async(self, prompt: str, **kwargs) -> ModelResponse:
        """Async version of generate using queue manager"""
        from local_agent.utils.queue_manager import queue_manager, RequestPriority
        
        # Submit to queue
        priority = kwargs.get('priority', RequestPriority.NORMAL)
        
        response_content = await queue_manager.submit(
            user_id=kwargs.get('user_id', 'anonymous'),
            session_id=kwargs.get('session_id', 'default'),
            prompt=prompt,
            priority=priority,
            metadata={"model": self.model}
        )
        
        # Parse response (queue returns string, need to reconstruct ModelResponse)
        # In a real scenario, we might want to capture more metadata from the queue
        return ModelResponse(
            content=response_content,
            provider="Ollama",
            model=self.model,
            tier=self.get_tier(),
            latency_ms=0,  # Recalculated if needed
            tokens_per_second=0
        )
