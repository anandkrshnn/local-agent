"""Abstract base class for all model providers"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

class ModelTier(Enum):
    TINY = "tiny"       # < 1B params, extremely fast
    SMALL = "small"     # 1-8B params, balanced
    MEDIUM = "medium"   # 8-30B params, powerful
    LARGE = "large"     # 30B+ params, best quality

@dataclass
class ModelResponse:
    """Standardized response from any model provider"""
    content: str
    provider: str
    model: str
    tier: ModelTier
    latency_ms: float
    tokens_per_second: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: Dict[str, Any] = None

class ModelProvider(ABC):
    """Abstract base class for model providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is ready"""
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def get_tier(self) -> ModelTier:
        """Get the tier of this provider's default model"""
        pass
    
    def get_estimated_latency_ms(self) -> float:
        """Estimated latency for this provider"""
        return 1000  # Default 1 second
