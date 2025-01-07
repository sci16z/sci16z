import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.system_monitor import SystemMonitor
from core.model_manager import ModelManager
from core.task_handler import TaskHandler

class TaskScheduler:
    def __init__(self, model_manager: ModelManager, system_monitor: SystemMonitor):
        self.logger = get_logger(__name__)
        self.model_manager = model_manager
        self.system_monitor = system_monitor
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        self.max_concurrent_tasks = 2
        self.resource_thresholds = {
            'memory': 0.8,  # 80% max memory usage
            'gpu_memory': 0.9,  # 90% max GPU memory
            'disk': 0.9  # 90% max disk usage
        }

    async def start(self):
        """Start task scheduler"""
        try:
            self.logger.info("Starting task scheduler")
            await asyncio.gather(
                self._process_queue(),
                self._monitor_resources()
            )
        except Exception as e:
            self.logger.error(f"Task scheduler error: {str(e)}")

    async def schedule_task(self, task: Dict[str, Any]) -> bool:
        """Schedule new task"""
        try:
            # Check resource availability
            if not await self._check_resources():
                self.logger.warning("Insufficient resources to schedule task")
                return False

            # Add task to queue
            await self.task_queue.put(task)
            self.logger.info(f"Task {task['id']} scheduled")
            return True

        except Exception as e:
            self.logger.error(f"Failed to schedule task: {str(e)}")
            return False

    async def _process_queue(self):
        """Process task queue"""
        while True:
            try:
                # Check running tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(5)
                    continue

                # Get next task
                task = await self.task_queue.get()
                
                # Start task processing
                task_handler = TaskHandler(self.model_manager)
                process_task = asyncio.create_task(task_handler.process_task(task))
                self.running_tasks[task['id']] = {
                    'task': process_task,
                    'handler': task_handler,
                    'start_time': datetime.now()
                }

                # Clean up completed task
                process_task.add_done_callback(
                    lambda _: self._cleanup_task(task['id'])
                )

            except Exception as e:
                self.logger.error(f"Task queue processing error: {str(e)}")
                await asyncio.sleep(5)

    async def _monitor_resources(self):
        """Monitor system resources"""
        while True:
            try:
                system_info = self.system_monitor.get_system_info()
                
                # Check resource thresholds
                if self._check_thresholds(system_info):
                    await self._handle_resource_pressure()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {str(e)}")
                await asyncio.sleep(60)

    def _check_thresholds(self, system_info: Dict[str, Any]) -> bool:
        """Check if resource usage exceeds thresholds"""
        try:
            memory_usage = float(system_info['memory']['percent'].strip('%')) / 100
            disk_usage = float(system_info['disk']['percent'].strip('%')) / 100
            
            if 'gpu' in system_info and system_info['gpu']['available']:
                gpu_memory = float(system_info['gpu']['memory']['used'].strip('GB'))
                gpu_total = float(system_info['gpu']['memory']['total'].strip('GB'))
                gpu_usage = gpu_memory / gpu_total
            else:
                gpu_usage = 0

            return (
                memory_usage > self.resource_thresholds['memory'] or
                gpu_usage > self.resource_thresholds['gpu_memory'] or
                disk_usage > self.resource_thresholds['disk']
            )
            
        except Exception as e:
            self.logger.error(f"Resource threshold check error: {str(e)}")
            return False

    async def _handle_resource_pressure(self):
        """Handle high resource usage"""
        try:
            # Stop accepting new tasks
            self.task_queue.put_nowait = lambda _: None
            
            # Wait for running tasks to complete
            if self.running_tasks:
                self.logger.info("Waiting for running tasks to complete")
                await asyncio.gather(*[
                    task_info['task'] 
                    for task_info in self.running_tasks.values()
                ])
                
            # Clear queue
            while not self.task_queue.empty():
                await self.task_queue.get()
                
            # Restore queue functionality
            self.task_queue.put_nowait = self.task_queue.put
            
            self.logger.info("Resource pressure handled")
            
        except Exception as e:
            self.logger.error(f"Resource pressure handling error: {str(e)}")

    def _cleanup_task(self, task_id: str):
        """Clean up completed task"""
        try:
            if task_id in self.running_tasks:
                task_info = self.running_tasks.pop(task_id)
                duration = datetime.now() - task_info['start_time']
                self.logger.info(
                    f"Task {task_id} completed in {duration.total_seconds():.1f}s"
                )
        except Exception as e:
            self.logger.error(f"Task cleanup error: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.running_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'resource_thresholds': self.resource_thresholds
        } 