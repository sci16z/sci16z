import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.logger import get_logger
from utils.task_queue import TaskQueue
from utils.process_pool import ProcessPool
from utils.system_monitor import SystemMonitor
from utils.task_status import TaskStatusManager
from core.task_handler import TaskHandler
from core.model_manager import ModelManager

class TaskScheduler:
    def __init__(self, model_manager: ModelManager):
        self.logger = get_logger(__name__)
        self.model_manager = model_manager
        self.system_monitor = SystemMonitor()
        self.status_manager = TaskStatusManager()
        self.task_queue = TaskQueue(self.status_manager)
        self.process_pool = ProcessPool(self.system_monitor)
        self.task_handlers = {}
        self.running = False
        self.scheduler_config = {
            'max_concurrent_tasks': 3,
            'queue_check_interval': 1.0,  # seconds
            'resource_check_interval': 30.0,  # seconds
            'min_memory_available': 2.0,  # GB
            'min_gpu_memory': 2.0,  # GB
            'task_timeout': 3600  # 1 hour
        }

    async def start(self):
        """Start task scheduler"""
        try:
            self.running = True
            self.logger.info("Starting task scheduler")
            
            # Start process pool
            await self.process_pool.start()
            
            # Start scheduler tasks
            await asyncio.gather(
                self._process_queue(),
                self._monitor_resources(),
                self._cleanup_tasks()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start task scheduler: {str(e)}")
            self.running = False
            raise

    async def stop(self):
        """Stop task scheduler"""
        try:
            self.running = False
            self.logger.info("Stopping task scheduler")
            
            # Stop process pool
            await self.process_pool.stop()
            
            # Cancel running tasks
            for task_id in list(self.task_handlers.keys()):
                await self.cancel_task(task_id)
                
        except Exception as e:
            self.logger.error(f"Failed to stop task scheduler: {str(e)}")

    async def schedule_task(self, task: Dict[str, Any], priority: bool = False) -> bool:
        """Schedule new task"""
        try:
            # Validate task
            if not self._validate_task(task):
                return False
                
            # Check resource availability
            if not await self._check_resources():
                self.logger.warning("Insufficient resources to schedule task")
                return False
                
            # Add to queue
            return await self.task_queue.enqueue(task, priority)
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task: {str(e)}")
            return False

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task execution"""
        try:
            # Check if task is running
            if task_id in self.task_handlers:
                handler = self.task_handlers[task_id]
                await handler.cancel()
                self.task_handlers.pop(task_id)
                
            # Cancel queued task
            return await self.task_queue.cancel_task(task_id)
            
        except Exception as e:
            self.logger.error(f"Failed to cancel task: {str(e)}")
            return False

    async def _process_queue(self):
        """Process task queue"""
        while self.running:
            try:
                # Check concurrent task limit
                if len(self.task_handlers) >= self.scheduler_config['max_concurrent_tasks']:
                    await asyncio.sleep(self.scheduler_config['queue_check_interval'])
                    continue
                    
                # Get next task
                task = await self.task_queue.dequeue()
                if not task:
                    await asyncio.sleep(self.scheduler_config['queue_check_interval'])
                    continue
                    
                # Create task handler
                handler = TaskHandler(self.model_manager)
                self.task_handlers[task['id']] = handler
                
                # Start task processing
                asyncio.create_task(self._execute_task(task, handler))
                
            except Exception as e:
                self.logger.error(f"Task queue processing error: {str(e)}")
                await asyncio.sleep(self.scheduler_config['queue_check_interval'])

    async def _execute_task(self, task: Dict[str, Any], handler: TaskHandler):
        """Execute task with handler"""
        try:
            # Process task
            result = await self.task_queue.process_task(task, handler.process_task)
            
            # Cleanup
            self.task_handlers.pop(task['id'], None)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution error: {str(e)}")
            self.task_handlers.pop(task['id'], None)
            return None

    async def _monitor_resources(self):
        """Monitor system resources"""
        while self.running:
            try:
                system_info = self.system_monitor.get_system_info()
                
                # Check memory usage
                memory_available = float(system_info['memory']['available'].strip('GB'))
                if memory_available < self.scheduler_config['min_memory_available']:
                    self.logger.warning("Low memory available")
                    await self._handle_resource_pressure()
                    
                # Check GPU memory if available
                if system_info.get('gpu', {}).get('available'):
                    gpu_memory = float(system_info['gpu']['memory']['free'].strip('GB'))
                    if gpu_memory < self.scheduler_config['min_gpu_memory']:
                        self.logger.warning("Low GPU memory available")
                        await self._handle_resource_pressure()
                        
                await asyncio.sleep(self.scheduler_config['resource_check_interval'])
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {str(e)}")
                await asyncio.sleep(self.scheduler_config['resource_check_interval'])

    async def _handle_resource_pressure(self):
        """Handle resource pressure"""
        try:
            # Stop accepting new tasks
            self.task_queue.queue.put_nowait = lambda _: None
            self.task_queue.priority_queue.put_nowait = lambda _: None
            
            # Wait for running tasks to complete
            if self.task_handlers:
                self.logger.info("Waiting for running tasks to complete")
                for handler in self.task_handlers.values():
                    await handler.wait()
                    
            # Restore queue functionality
            self.task_queue.queue.put_nowait = self.task_queue.queue.put
            self.task_queue.priority_queue.put_nowait = self.task_queue.priority_queue.put
            
        except Exception as e:
            self.logger.error(f"Resource pressure handling error: {str(e)}")

    async def _cleanup_tasks(self):
        """Clean up timed out tasks"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check running tasks
                for task_id, handler in list(self.task_handlers.items()):
                    if (current_time - handler.start_time).total_seconds() > self.scheduler_config['task_timeout']:
                        self.logger.warning(f"Task {task_id} timed out")
                        await self.cancel_task(task_id)
                        
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Task cleanup error: {str(e)}")
                await asyncio.sleep(60)

    def _validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task configuration"""
        required_fields = ['id', 'type', 'config']
        return all(field in task for field in required_fields)

    async def _check_resources(self) -> bool:
        """Check resource availability"""
        try:
            system_info = self.system_monitor.get_system_info()
            
            # Check memory
            memory_available = float(system_info['memory']['available'].strip('GB'))
            if memory_available < self.scheduler_config['min_memory_available']:
                return False
                
            # Check GPU if required
            if system_info.get('gpu', {}).get('available'):
                gpu_memory = float(system_info['gpu']['memory']['free'].strip('GB'))
                if gpu_memory < self.scheduler_config['min_gpu_memory']:
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Resource check error: {str(e)}")
            return False

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.running,
            'active_tasks': len(self.task_handlers),
            'queue_status': self.task_queue.get_queue_status(),
            'pool_status': self.process_pool.get_pool_status(),
            'config': self.scheduler_config
        } 