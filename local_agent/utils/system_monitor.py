"""
Real-time System Monitoring
Collects CPU, RAM, GPU metrics for observability
"""

import psutil
import threading
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SystemMetrics:
    """System metrics snapshot"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_used_gb: float
    disk_total_gb: float
    gpu_available: bool = False
    gpu_utilization: float = 0.0
    gpu_memory_used_gb: float = 0.0

class SystemMonitor:
    """
    System resource monitor with historical tracking
    """
    
    def __init__(self, history_size: int = 3600):  # 1 hour at 1 sample/sec
        self.history: list = []
        self.history_size = history_size
        self._monitoring = False
        self._thread = None
        self._listeners = []
    
    def start_monitoring(self, interval_seconds: float = 1.0):
        """Start background monitoring thread"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,), daemon=True)
        self._thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._monitoring:
            metrics = self.get_current_metrics()
            self.history.append(metrics)
            
            # Trim history
            if len(self.history) > self.history_size:
                self.history = self.history[-self.history_size:]
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    listener(metrics)
                except:
                    pass
            
            time.sleep(interval)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_total_gb=memory.total / (1024**3),
            disk_used_gb=disk.used / (1024**3),
            disk_total_gb=disk.total / (1024**3)
        )
        
        # Try to get GPU metrics
        try:
            from .gpu import GPUAccelerator
            gpu = GPUAccelerator()
            info = gpu.get_device_info()
            metrics.gpu_available = info['has_cuda'] or info['has_mps']
            # Note: GPU utilization requires nvidia-ml-py3 or similar
        except:
            pass
        
        return metrics
    
    def get_metrics_history(self, seconds: int = 60) -> list:
        """Get metrics history for the last N seconds"""
        cutoff = time.time() - seconds
        return [m for m in self.history if m.timestamp > cutoff]
    
    def get_current_snapshot(self) -> Dict:
        """Get current metrics as dictionary"""
        metrics = self.get_current_metrics()
        return {
            "timestamp": metrics.timestamp,
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_used_gb": round(metrics.memory_used_gb, 2),
            "memory_total_gb": round(metrics.memory_total_gb, 2),
            "disk_used_gb": round(metrics.disk_used_gb, 2),
            "disk_total_gb": round(metrics.disk_total_gb, 2),
            "gpu_available": metrics.gpu_available
        }
    
    def add_listener(self, callback):
        """Add a callback for real-time metrics updates"""
        self._listeners.append(callback)
    
    def remove_listener(self, callback):
        """Remove a callback"""
        if callback in self._listeners:
            self._listeners.remove(callback)

# Singleton instance
system_monitor = SystemMonitor()
system_monitor.start_monitoring()
