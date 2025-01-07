from __future__ import annotations
import os
import psutil
from typing import Dict, Any
from utils.logger import get_logger
from utils.gpu_monitor import GPUMonitor

class SystemMonitor:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.gpu_monitor = GPUMonitor()
        self.min_memory = 8  # GB
        self.min_disk_space = 10  # GB

    def check_system_requirements(self) -> bool:
        """Check if system meets minimum requirements"""
        try:
            # Check memory
            memory_ok = self._check_memory()
            
            # Check disk space
            disk_ok = self._check_disk_space()
            
            # Check GPU
            gpu_ok = self.gpu_monitor.check_gpu()
            
            return memory_ok and disk_ok and gpu_ok
            
        except Exception as e:
            self.logger.error(f"System check failed: {str(e)}")
            return False

    def _check_memory(self) -> bool:
        """Check available memory"""
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            
            if available_gb < self.min_memory:
                self.logger.warning(f"Insufficient memory: {available_gb:.1f}GB available")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Memory check failed: {str(e)}")
            return False

    def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            disk = psutil.disk_usage('/')
            available_gb = disk.free / (1024 ** 3)
            
            if available_gb < self.min_disk_space:
                self.logger.warning(f"Insufficient disk space: {available_gb:.1f}GB available")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Disk check failed: {str(e)}")
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            gpu_info = self.gpu_monitor.get_gpu_info()
            
            return {
                'cpu': {
                    'usage': f"{cpu_percent}%",
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'total': f"{memory.total / (1024**3):.1f}GB",
                    'available': f"{memory.available / (1024**3):.1f}GB",
                    'percent': f"{memory.percent}%"
                },
                'disk': {
                    'total': f"{disk.total / (1024**3):.1f}GB",
                    'free': f"{disk.free / (1024**3):.1f}GB",
                    'percent': f"{disk.percent}%"
                },
                'gpu': gpu_info
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {str(e)}")
            return {} 