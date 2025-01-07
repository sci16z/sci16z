from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatusManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.active_tasks = {}
        self.task_history = {}
        self.max_history = 100

    def create_task(self, task_id: str, task_type: str) -> Dict[str, Any]:
        """Create new task record"""
        task = {
            'id': task_id,
            'type': task_type,
            'status': TaskStatus.PENDING,
            'progress': 0,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        self.active_tasks[task_id] = task
        return task

    def update_task(self, task_id: str, status: TaskStatus, progress: int = None) -> Optional[Dict[str, Any]]:
        """Update task status"""
        if task_id not in self.active_tasks:
            self.logger.warning(f"Task {task_id} not found")
            return None

        task = self.active_tasks[task_id]
        task['status'] = status
        task['updated_at'] = datetime.now()
        
        if progress is not None:
            task['progress'] = progress

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self._move_to_history(task_id)

        return task

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        return self.active_tasks.get(task_id) or self.task_history.get(task_id)

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all active tasks"""
        return self.active_tasks

    def get_task_history(self, limit: int = None) -> Dict[str, Dict[str, Any]]:
        """Get task history"""
        if limit:
            return dict(list(self.task_history.items())[:limit])
        return self.task_history

    def _move_to_history(self, task_id: str):
        """Move task to history"""
        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)
            self.task_history[task_id] = task
            self._cleanup_history()

    def _cleanup_history(self):
        """Clean up old history records"""
        if len(self.task_history) > self.max_history:
            sorted_history = sorted(
                self.task_history.items(),
                key=lambda x: x[1]['updated_at']
            )
            self.task_history = dict(sorted_history[-self.max_history:])

    def cleanup_old_history(self, days: int = 7):
        """Clean up history older than specified days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.task_history = {
            k: v for k, v in self.task_history.items()
            if v['updated_at'].timestamp() > cutoff
        } 