"""
GPU Detection and Management Utilities for Sprint 6
"""

import sys
from pathlib import Path

def check_gpu_availability():
    """Warn user if GPU not available for GPU-intensive features"""
    try:
        import torch
        if not torch.cuda.is_available():
            print("⚠️ WARNING: No NVIDIA GPU detected via CUDA. Fine-tuning and Vision will be VERY slow.")
            print("   Consider using cloud GPU or upgrading hardware if you experience timeouts.")
            return False
        
        device_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✅ GPU detected: {device_name} ({vram_gb:.1f}GB VRAM)")
        
        if vram_gb < 8:
            print(f"⚠️ Low VRAM detected: {vram_gb:.1f}GB. Fine-tuning might fail without lower batch sizes.")
            
        return True
    except ImportError:
        print("⚠️ PyTorch not installed properly. GPU detection skipped.")
        return False

def check_disk_space(required_gb: int = 10):
    """Ensure sufficient disk space for fine-tuned models and checkpoints"""
    import shutil
    # Get free space in the directory where models are stored
    models_dir = Path("./fine_tuned_models")
    models_dir.mkdir(exist_ok=True)
    
    usage = shutil.disk_usage(models_dir)
    free_gb = usage.free / (1024**3)
    
    if free_gb < required_gb:
        print(f"⚠️ Low disk space: {free_gb:.1f}GB free, {required_gb}GB recommended for Sprint 6.")
        return False
    
    print(f"✅ Sufficient disk space: {free_gb:.1f}GB free.")
    return True

if __name__ == "__main__":
    check_gpu_availability()
    check_disk_space()
