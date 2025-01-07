from __future__ import annotations
import platform
import psutil
from typing import Dict, Any
from utils.logger import get_logger

class GPUMonitor:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.backend = None
        self._init_backend()

    def _init_backend(self):
        """Initialize GPU monitoring backend"""
        try:
            import torch
            if torch.cuda.is_available():
                self.backend = "cuda"
                return
                
            try:
                import tensorflow as tf
                if tf.config.list_physical_devices('GPU'):
                    self.backend = "tensorflow"
                    return
            except ImportError:
                pass
                
            self.backend = "cpu"
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPU monitor: {str(e)}")
            self.backend = "cpu"

    def check_gpu(self) -> bool:
        """Check GPU availability"""
        return self.backend != "cpu"

    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        try:
            if self.backend == "cuda":
                return self._get_cuda_info()
            elif self.backend == "tensorflow":
                return self._get_tensorflow_info()
            else:
                return {
                    'available': False,
                    'backend': 'cpu'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get GPU info: {str(e)}")
            return {
                'available': False,
                'error': str(e)
            }

    def _get_cuda_info(self) -> Dict[str, Any]:
        """Get CUDA GPU information"""
        import torch
        try:
            return {
                'available': True,
                'backend': 'cuda',
                'device_count': torch.cuda.device_count(),
                'device_name': torch.cuda.get_device_name(0),
                'memory': {
                    'allocated': f"{torch.cuda.memory_allocated(0) / 1024**2:.1f}MB",
                    'cached': f"{torch.cuda.memory_reserved(0) / 1024**2:.1f}MB"
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get CUDA info: {str(e)}")
            return {'available': False, 'error': str(e)}

    def _get_tensorflow_info(self) -> Dict[str, Any]:
        """Get TensorFlow GPU information"""
        import tensorflow as tf
        try:
            gpus = tf.config.list_physical_devices('GPU')
            return {
                'available': True,
                'backend': 'tensorflow',
                'device_count': len(gpus),
                'devices': [gpu.name for gpu in gpus]
            }
        except Exception as e:
            self.logger.error(f"Failed to get TensorFlow info: {str(e)}")
            return {'available': False, 'error': str(e)} 