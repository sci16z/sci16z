import os
import psutil
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.gpu_monitor import GPUMonitor
from utils.metrics_collector import MetricsCollector

class ResourceManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.gpu_monitor = GPUMonitor()
        self.metrics = MetricsCollector()
        self.resource_limits = {
            'memory': 0.9,      # 90% max memory usage
            'gpu_memory': 0.95, # 95% max GPU memory
            'disk': 0.95,       # 95% max disk usage
            'cpu': 0.8         # 80% max CPU usage
        }
        self.monitoring = False

    async def start_monitoring(self):
        """Start resource monitoring"""
        try:
            self.monitoring = True
            self.logger.info("Starting resource monitoring")
            
            while self.monitoring:
                # Collect current metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                await self.metrics.store(metrics)
                
                # Check resource limits
                await self._check_limits(metrics)
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
        except Exception as e:
            self.logger.error(f"Resource monitoring error: {str(e)}")
            self.monitoring = False

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        self.logger.info("Resource monitoring stopped")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # GPU metrics
            gpu_info = self.gpu_monitor.get_gpu_info()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'usage_percent': cpu_percent,
                    'frequency_mhz': cpu_freq.current if cpu_freq else None,
                    'core_count': cpu_count
                },
                'memory': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_percent': memory.percent,
                    'swap_used_percent': swap.percent
                },
                'disk': {
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_percent': disk.percent,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes
                },
                'gpu': gpu_info
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            return {}

    async def _check_limits(self, metrics: Dict[str, Any]) -> bool:
        """Check if resource usage exceeds limits"""
        try:
            violations = []
            
            # Check CPU usage
            if metrics.get('cpu', {}).get('usage_percent', 0) > self.resource_limits['cpu'] * 100:
                violations.append('CPU')
                
            # Check memory usage
            if metrics.get('memory', {}).get('used_percent', 0) > self.resource_limits['memory'] * 100:
                violations.append('Memory')
                
            # Check disk usage
            if metrics.get('disk', {}).get('used_percent', 0) > self.resource_limits['disk'] * 100:
                violations.append('Disk')
                
            # Check GPU usage if available
            gpu_info = metrics.get('gpu', {})
            if gpu_info.get('available', False):
                gpu_memory = gpu_info.get('memory', {})
                used = float(gpu_memory.get('used', '0').strip('GB'))
                total = float(gpu_memory.get('total', '1').strip('GB'))
                if used / total > self.resource_limits['gpu_memory']:
                    violations.append('GPU')
            
            if violations:
                self.logger.warning(f"Resource limits exceeded: {', '.join(violations)}")
                await self._handle_violations(violations)
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Resource limit check error: {str(e)}")
            return False

    async def _handle_violations(self, violations: list):
        """Handle resource limit violations"""
        try:
            # Log violation details
            self.logger.warning(f"Handling resource violations: {violations}")
            
            # Collect process information
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 50 or pinfo['memory_percent'] > 50:
                        processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by resource usage
            processes.sort(key=lambda x: x['cpu_percent'] + x['memory_percent'], reverse=True)
            
            # Log top resource consumers
            if processes:
                self.logger.warning("Top resource consuming processes:")
                for proc in processes[:5]:
                    self.logger.warning(
                        f"PID {proc['pid']} ({proc['name']}): "
                        f"CPU {proc['cpu_percent']}%, Mem {proc['memory_percent']}%"
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to handle resource violations: {str(e)}")

    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status"""
        try:
            metrics = self._collect_metrics()
            return {
                'status': 'healthy' if self.monitoring else 'not_monitoring',
                'metrics': metrics,
                'limits': self.resource_limits,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get resource status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 