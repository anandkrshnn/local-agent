# localagent/models/ollama.py
import json
import re
import requests
from typing import Tuple, Optional, Dict, List

class OllamaClient:
    """Ollama client with proper system prompt support"""

    def __init__(self, model: str = "phi3:mini"):
        self.model = model
        self.history: List[Dict] = []

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Simple text generation"""
        return self._call(prompt, temperature=temperature, system=None)

    def generate_structured(self, prompt: str, system: Optional[str] = None, temperature: float = 0.1) -> Tuple[str, Optional[Dict]]:
        """Generate with optional system prompt and attempt to parse JSON"""
        response = self._call(prompt, temperature=temperature, system=system)
        
        # Try to extract JSON
        try:
            parsed = json.loads(response)
            return response, parsed
        except json.JSONDecodeError:
            # Fallback regex extraction
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    parsed = json.loads(match.group())
                    return response, parsed
                except:
                    pass
            return response, None

    def _call(self, prompt: str, temperature: float, system: Optional[str] = None) -> str:
        """Core call with proper system message handling"""
        messages = []

        # Add system message if provided (this is the key fix)
        if system:
            messages.append({"role": "system", "content": system})

        # Add conversation history
        messages.extend(self.history)

        # Add current user prompt
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }

        try:
            resp = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]

            # Update history (keep system out of history to avoid duplication)
            self.history.append({"role": "user", "content": prompt})
            self.history.append({"role": "assistant", "content": content})

            if len(self.history) > 15:
                self.history = self.history[-15:]

            return content
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")

    def clear_history(self):
        self.history.clear()
