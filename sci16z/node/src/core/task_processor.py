from __future__ import annotations
import asyncio
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.metrics_collector import MetricsCollector
from utils.model_downloader import ModelDownloader
from utils.wallet import WalletManager

class TaskProcessor:
    def __init__(self, wallet_manager: WalletManager):
        self.logger = get_logger(__name__)
        self.metrics = MetricsCollector()
        self.model_downloader = ModelDownloader()
        self.wallet_manager = wallet_manager
        self.running_tasks = {}

    async def process_task(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single task"""
        try:
            task_id = task['id']
            self.running_tasks[task_id] = task
            
            # Record start metrics
            await self.metrics.record_metric(
                'task_start',
                1,
                {'task_id': task_id, 'type': task['type']}
            )

            # Download required model if needed
            if 'model_id' in task:
                model_path = await self.model_downloader.download_model(task['model_id'])
                if not model_path:
                    raise Exception(f"Failed to download model {task['model_id']}")

            # Process task based on type
            result = await self._execute_task(task)

            # Update metrics
            await self.metrics.record_metric(
                'task_complete',
                1,
                {'task_id': task_id, 'success': True}
            )

            # Update wallet balance
            if 'reward' in task:
                await self.wallet_manager.update_balance()

            return result

        except Exception as e:
            self.logger.error(f"Task processing error: {str(e)}")
            await self.metrics.record_metric(
                'task_error',
                1,
                {'task_id': task_id, 'error': str(e)}
            )
            return None
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task based on type"""
        task_type = task['type']
        
        if task_type == 'inference':
            return await self._run_inference(task)
        elif task_type == 'training':
            return await self._run_training(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _run_inference(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run inference task"""
        # Implementation here
        pass

    async def _run_training(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run training task"""
        # Implementation here
        pass

    def get_running_tasks(self) -> Dict[str, Any]:
        """Get currently running tasks"""
        return {
            task_id: {
                'type': task['type'],
                'start_time': task['start_time'],
                'status': task['status']
            }
            for task_id, task in self.running_tasks.items()
        } 