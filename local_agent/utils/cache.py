"""Response caching for Local Agent v4.0"""

import pickle
import hashlib
import os
from datetime import datetime, timedelta
from typing import Any, Optional

class ModelCache:
    """Persistent cache for model responses"""
    
    def __init__(self, cache_dir: str = ".agent_cache", max_size: int = 1000):
        self.cache_dir = cache_dir
        self.max_size = max_size
        os.makedirs(cache_dir, exist_ok=True)
        self.memory_cache = {}
    
    def _get_key(self, prompt: str, provider: str, model: str) -> str:
        """Generate unique cache key"""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, prompt: str, provider: str, model: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._get_key(prompt, provider, model)
        
        # Check memory cache
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if datetime.now() < entry['expiry']:
                return entry['data']
        
        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                    if datetime.now() < entry['expiry']:
                        self.memory_cache[key] = entry
                        return entry['data']
            except:
                pass
                
        return None
    
    def set(self, prompt: str, provider: str, model: str, data: Any, ttl_hours: int = 24):
        """Store response in cache"""
        key = self._get_key(prompt, provider, model)
        entry = {
            "data": data,
            "expiry": datetime.now() + timedelta(hours=ttl_hours),
            "timestamp": datetime.now()
        }
        
        self.memory_cache[key] = entry
        
        # Save to disk
        cache_file = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except:
            pass
            
    def clear(self):
        """Clear all caches"""
        self.memory_cache.clear()
        for f in os.listdir(self.cache_dir):
            if f.endswith(".pkl"):
                os.remove(os.path.join(self.cache_dir, f))
