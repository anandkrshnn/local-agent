"""
Multi-modal Vision Manager for Sprint 6
Handles image preprocessing and LLaVA integration
"""

import os
import base64
import io
from pathlib import Path
from typing import Dict, Optional, List
from PIL import Image

class VisionManager:
    """
    Handles image processing and vision model interactions
    Supports LLaVA (via Ollama) and local OCR fallback
    """
    
    def __init__(self, vision_model: str = "llava:latest", max_image_size: int = 1024):
        self.vision_model = vision_model
        self.max_image_size = max_image_size
        
    def preprocess_image(self, image_data: bytes, format: str = 'JPEG') -> str:
        """Resize and optimize image before encoding to Base64"""
        img = Image.open(io.BytesIO(image_data))
        
        # Resize if too large
        if max(img.size) > self.max_image_size:
            ratio = self.max_image_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB (required for JPEG)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def analyze_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> str:
        """Analyze an image using the vision model"""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        b64_image = self.preprocess_image(image_bytes)
        
        # This will be called by the broker/orchestrator via OllamaProvider
        return {
            "model": self.vision_model,
            "prompt": prompt,
            "images": [b64_image]
        }

    def extract_text(self, image_path: str) -> str:
        """OCR fallback using pytesseract"""
        try:
            import pytesseract
            img = Image.open(image_path)
            return pytesseract.image_to_string(img)
        except ImportError:
            return "⚠️ OCR not available. Install pytesseract."
        except Exception as e:
            return f"❌ OCR error: {e}"

# Singleton instance
vision_manager = VisionManager()
