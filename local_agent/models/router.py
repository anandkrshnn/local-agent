"""Intelligent model router for multi-provider setup"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from .base import ModelProvider, ModelResponse, ModelTier
from .ollama import OllamaProvider

@dataclass
class RoutingRule:
    """Rule for routing to specific providers"""
    intent_patterns: List[str]
    preferred_tier: ModelTier
    min_latency_ms: float = 0
    max_latency_ms: float = float('inf')

class ModelRouter:
    """Intelligently routes requests to the best available provider"""
    
    def __init__(self):
        self.providers: List[ModelProvider] = []
        self.routing_rules = self._default_rules()
        self._init_providers()
    
    def _default_rules(self) -> List[RoutingRule]:
        return [
            RoutingRule(
                intent_patterns=["hello", "hi", "greeting", "who are you"],
                preferred_tier=ModelTier.TINY,
                max_latency_ms=500
            ),
            RoutingRule(
                intent_patterns=["read", "write", "file", "search", "memory"],
                preferred_tier=ModelTier.SMALL,
                max_latency_ms=2000
            ),
            RoutingRule(
                intent_patterns=["explain", "analyze", "compare", "summarize"],
                preferred_tier=ModelTier.MEDIUM,
                max_latency_ms=5000
            ),
            RoutingRule(
                intent_patterns=["code", "program", "debug", "function"],
                preferred_tier=ModelTier.MEDIUM,
                max_latency_ms=5000
            )
        ]
    
    def _init_providers(self):
        """Initialize all available providers in priority order"""
        # Local providers first
        ollama = OllamaProvider()
        if ollama.is_available():
            self.providers.append(ollama)
        
        # Try to import and initialize cloud providers
        if os.getenv("OPENAI_API_KEY"):
            try:
                from .openai import OpenAIProvider
                self.providers.append(OpenAIProvider())
            except ImportError:
                pass
        
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from .anthropic import AnthropicProvider
                self.providers.append(AnthropicProvider())
            except ImportError:
                pass
        
        if os.getenv("GROQ_API_KEY"):
            try:
                from .groq import GroqProvider
                self.providers.append(GroqProvider())
            except ImportError:
                pass
    
    def _get_intent_category(self, prompt: str) -> str:
        """Categorize intent from prompt"""
        prompt_lower = prompt.lower()
        for rule in self.routing_rules:
            for pattern in rule.intent_patterns:
                if pattern in prompt_lower:
                    return rule
        return self.routing_rules[1]  # Default to small tier
    
    def route(self, prompt: str, force_provider: str = None) -> ModelResponse:
        """Route prompt to the best available provider"""
        
        # If specific provider requested
        if force_provider:
            for provider in self.providers:
                if provider.__class__.__name__.lower() == force_provider.lower():
                    return provider.generate(prompt)
        
        # Get intent category
        rule = self._get_intent_category(prompt)
        
        # Find best provider based on tier preference
        best_provider = None
        best_score = -1
        
        for provider in self.providers:
            if not provider.is_available():
                continue
            
            # Score based on tier match and latency
            tier_match = 1.0 if provider.get_tier() == rule.preferred_tier else 0.5
            latency_score = 1.0 / (provider.get_estimated_latency_ms() / 1000)
            
            score = tier_match * 0.7 + latency_score * 0.3
            
            if score > best_score:
                best_score = score
                best_provider = provider
        
        if not best_provider:
            raise Exception("No model providers available")
        
        return best_provider.generate(prompt)
    
    def get_status(self) -> Dict:
        """Get status of all providers"""
        return {
            "providers": [
                {
                    "name": p.__class__.__name__,
                    "available": p.is_available(),
                    "models": p.get_models()[:5],
                    "tier": p.get_tier().value,
                    "estimated_latency_ms": p.get_estimated_latency_ms()
                }
                for p in self.providers
            ]
        }
