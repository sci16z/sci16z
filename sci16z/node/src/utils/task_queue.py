import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from utils.logger import get_logger
from utils.task_status import TaskStatus, TaskStatusManager

class TaskQueue:
    def __init__(self, status_manager: TaskStatusManager):
        self.logger = get_logger(__name__)
        self.status_manager = status_manager
        self.queue = asyncio.Queue()
        self.priority_queue = asyncio.PriorityQueue()
        self.processing = {}
        self.callbacks = {}
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    async def enqueue(self, task: Dict[str, Any], priority: bool = False) -> bool:
        """Add task to queue"""
        try:
            task_id = task.get('id')
            if not task_id:
                self.logger.error("Task missing ID")
                return False

            # Create task record
            self.status_manager.create_task(
                task_id,
                task.get('type', 'unknown')
            )

            # Add to appropriate queue
            if priority:
                await self.priority_queue.put((1, task))
            else:
                await self.queue.put((2, task))

            self.logger.info(f"Task {task_id} enqueued (priority: {priority})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to enqueue task: {str(e)}")
            return False

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        try:
            # Check priority queue first
            if not self.priority_queue.empty():
                _, task = await self.priority_queue.get()
                return task

            # Then check regular queue
            if not self.queue.empty():
                _, task = await self.queue.get()
                return task

            return None

        except Exception as e:
            self.logger.error(f"Failed to dequeue task: {str(e)}")
            return None

    async def process_task(self, task: Dict[str, Any], processor: Callable):
        """Process task with retry logic"""
        task_id = task['id']
        retries = 0

        while retries < self.max_retries:
            try:
                # Update status to running
                self.status_manager.update_task(
                    task_id,
                    TaskStatus.RUNNING
                )

                # Process task
                self.processing[task_id] = {
                    'task': task,
                    'start_time': datetime.now()
                }

                result = await processor(task)

                # Handle success
                self.status_manager.update_task(
                    task_id,
                    TaskStatus.COMPLETED
                )

                # Execute callback if exists
                if task_id in self.callbacks:
                    await self.callbacks[task_id](result)

                return result

            except Exception as e:
                retries += 1
                self.logger.error(
                    f"Task {task_id} failed (attempt {retries}): {str(e)}"
                )

                if retries < self.max_retries:
                    await asyncio.sleep(self.retry_delay * retries)
                else:
                    # Mark as failed after all retries
                    self.status_manager.update_task(
                        task_id,
                        TaskStatus.FAILED
                    )

        return None

    def register_callback(self, task_id: str, callback: Callable):
        """Register callback for task completion"""
        self.callbacks[task_id] = callback

    def remove_callback(self, task_id: str):
        """Remove task callback"""
        self.callbacks.pop(task_id, None)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel queued or processing task"""
        try:
            # Check processing tasks
            if task_id in self.processing:
                self.status_manager.update_task(
                    task_id,
                    TaskStatus.CANCELLED
                )
                self.processing.pop(task_id)
                return True

            # Check queues
            for queue in [self.queue, self.priority_queue]:
                tasks = []
                while not queue.empty():
                    priority, task = await queue.get()
                    if task['id'] != task_id:
                        tasks.append((priority, task))
                
                # Restore other tasks
                for task_item in tasks:
                    await queue.put(task_item)

            self.status_manager.update_task(
                task_id,
                TaskStatus.CANCELLED
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel task: {str(e)}")
            return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information"""
        return {
            'priority_queue_size': self.priority_queue.qsize(),
            'regular_queue_size': self.queue.qsize(),
            'processing_tasks': len(self.processing),
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        } 