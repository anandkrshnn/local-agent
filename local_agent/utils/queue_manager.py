"""
Priority-based Request Queue Manager for Ollama Concurrency
Handles multiple concurrent requests without overwhelming the local model
"""

import asyncio
import heapq
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class RequestPriority(Enum):
    CRITICAL = 1    # System commands, confirmations
    HIGH = 2        # User interactions, chat
    NORMAL = 3      # Background tasks
    LOW = 4         # Batch processing, analytics

@dataclass
class QueuedRequest:
    """Request waiting in queue"""
    priority: int
    timestamp: float
    user_id: str
    session_id: str
    prompt: str
    future: asyncio.Future
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Heap comparison - lower priority number = higher priority"""
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority

class RequestQueueManager:
    """
    Singleton request queue manager for Ollama.
    Ensures fair queuing with priority support.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.queue: List[QueuedRequest] = []
            self.active_requests = 0
            self.max_concurrent = 1  # Ollama is single-threaded
            self.queue_timeout = 180  # Increased for slow local models
            self.total_processed = 0
            self.total_errors = 0
            self._lock = asyncio.Lock()
            self._processor_task = None
            self._stats = {
                "avg_wait_time": 0,
                "avg_process_time": 0,
                "queue_length": 0
            }
    
    async def start(self):
        """Start the background queue processor"""
        if self._processor_task is None or self._processor_task.done():
            self._processor_task = asyncio.create_task(self._process_queue())
    
    async def submit(self, 
                     user_id: str, 
                     session_id: str, 
                     prompt: str,
                     priority: RequestPriority = RequestPriority.NORMAL,
                     metadata: Dict[str, Any] = None) -> str:
        """
        Submit a request to the queue
        
        Args:
            user_id: User identifier
            session_id: Session identifier  
            prompt: The prompt to process
            priority: Request priority (affects queue order)
            metadata: Additional metadata for tracking
        
        Returns:
            Model response as string
        
        Raises:
            TimeoutError: If request times out in queue
        """
        future = asyncio.Future()
        
        request = QueuedRequest(
            priority=priority.value if hasattr(priority, 'value') else RequestPriority.NORMAL.value,
            timestamp=time.time(),
            user_id=user_id,
            session_id=session_id,
            prompt=prompt,
            future=future,
            metadata=metadata or {}
        )
        
        submit_time = time.time()
        
        async with self._lock:
            heapq.heappush(self.queue, request)
            self._stats["queue_length"] = len(self.queue)
        
        # Ensure processor is running
        await self.start()
        
        try:
            response = await asyncio.wait_for(future, timeout=self.queue_timeout)
            wait_time = time.time() - submit_time
            self._update_stats(wait_time, True)
            return response
        except asyncio.TimeoutError:
            self.total_errors += 1
            self._update_stats(time.time() - submit_time, False)
            if not future.done():
                future.cancel()
            raise Exception(f"Request timeout after {self.queue_timeout}s. Queue length: {len(self.queue)}")
        except Exception as e:
            self.total_errors += 1
            raise
    
    async def _process_queue(self):
        """Background task to process queued requests"""
        while True:
            try:
                await self._process_next()
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue processor error: {e}")
                await asyncio.sleep(1)
    
    async def _process_next(self):
        """Process the next request in queue"""
        async with self._lock:
            if self.active_requests >= self.max_concurrent:
                return
            
            if not self.queue:
                return
            
            request = heapq.heappop(self.queue)
            self.active_requests += 1
            self._stats["queue_length"] = len(self.queue)
        
        # Process request
        try:
            process_start = time.time()
            
            # Execute the actual model call
            from local_agent.models.ollama import OllamaProvider
            provider = OllamaProvider()
            
            # Run sync code in thread pool
            response = await asyncio.to_thread(
                provider.generate, 
                request.prompt,
                timeout=self.queue_timeout
            )
            
            process_time = time.time() - process_start
            self.total_processed += 1
            
            # Set result
            if not request.future.done():
                request.future.set_result(response.content)
            
        except Exception as e:
            if not request.future.done():
                if request.retry_count < 2:
                    # Retry with backoff
                    request.retry_count += 1
                    async with self._lock:
                        heapq.heappush(self.queue, request)
                else:
                    request.future.set_exception(e)
        finally:
            async with self._lock:
                self.active_requests -= 1
    
    def _update_stats(self, wait_time: float, success: bool):
        """Update queue statistics"""
        # Simple moving average
        alpha = 0.1
        if success:
            self._stats["avg_wait_time"] = alpha * wait_time + (1 - alpha) * self._stats["avg_wait_time"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "active_requests": self.active_requests,
            "queue_length": self._stats["queue_length"],
            "total_processed": self.total_processed,
            "total_errors": self.total_errors,
            "avg_wait_time_ms": self._stats["avg_wait_time"] * 1000,
            "max_concurrent": self.max_concurrent
        }
    
    async def clear(self):
        """Clear all pending requests (for shutdown)"""
        async with self._lock:
            for request in self.queue:
                if not request.future.done():
                    request.future.set_exception(Exception("System shutdown"))
            self.queue.clear()
            self.active_requests = 0

# Singleton instance
queue_manager = RequestQueueManager()
