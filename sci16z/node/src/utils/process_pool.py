from __future__ import annotations
import os
import asyncio
import multiprocessing as mp
from typing import Dict, Any, Optional, List, Callable, TypeVar
from datetime import datetime
from utils.logger import get_logger
from utils.system_monitor import SystemMonitor

class ProcessPool:
    def __init__(self, system_monitor: SystemMonitor):
        self.system_monitor = system_monitor
        self.max_workers = max(1, mp.cpu_count() - 1)
        self.workers = {}
        self.tasks = {}
        self.results = {}
        self._stop_event = mp.Event()
        self._logger = None  # 将在每个进程中初始化

    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_logger(__name__)
        return self._logger

    async def start(self):
        """Start process pool"""
        try:
            self.logger.info(f"Starting process pool with {self.max_workers} workers")
            for i in range(self.max_workers):
                await self._start_worker(i)
        except Exception as e:
            self.logger.error(f"Failed to start process pool: {str(e)}")
            raise

    async def stop(self):
        """Stop process pool"""
        try:
            self._stop_event.set()
            for worker_id, worker in self.workers.items():
                worker['process'].terminate()
                worker['process'].join()
            self.workers.clear()
            self.logger.info("Process pool stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop process pool: {str(e)}")

    async def submit(self, task_id: str, func: Callable, *args, **kwargs) -> bool:
        """Submit task to process pool"""
        try:
            # Find available worker
            worker_id = await self._get_available_worker()
            if worker_id is None:
                self.logger.warning("No available workers")
                return False

            # Prepare task
            task = {
                'id': task_id,
                'function': func,
                'args': args,
                'kwargs': kwargs,
                'start_time': datetime.now()
            }
            self.tasks[task_id] = task

            # Send task to worker
            worker = self.workers[worker_id]
            worker['task_queue'].put(task)
            worker['busy'] = True

            self.logger.info(f"Task {task_id} submitted to worker {worker_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to submit task: {str(e)}")
            return False

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Get task result"""
        try:
            start_time = datetime.now()
            while True:
                if task_id in self.results:
                    result = self.results.pop(task_id)
                    self.tasks.pop(task_id, None)
                    return result

                if timeout:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > timeout:
                        return None

                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Failed to get task result: {str(e)}")
            return None

    async def _start_worker(self, worker_id: int):
        """Start worker process"""
        try:
            task_queue = mp.Queue()
            result_queue = mp.Queue()

            process = mp.Process(
                target=self._worker_process,
                args=(worker_id, task_queue, result_queue, self._stop_event)
            )
            process.start()

            self.workers[worker_id] = {
                'process': process,
                'task_queue': task_queue,
                'result_queue': result_queue,
                'busy': False
            }

            # Start result collector
            asyncio.create_task(self._collect_results(worker_id))

        except Exception as e:
            self.logger.error(f"Failed to start worker {worker_id}: {str(e)}")
            raise

    def _worker_process(self, worker_id: int, task_queue: 'mp.Queue', 
                       result_queue: 'mp.Queue', stop_event: 'mp.Event'): # type: ignore
        """Worker process function"""
        # 在worker进程中初始化logger
        self._logger = get_logger(f"{__name__}.worker{worker_id}")
        while not stop_event.is_set():
            try:
                task = task_queue.get()
                if task is None:
                    break

                # Execute task
                result = task['function'](*task['args'], **task['kwargs'])
                
                # Send result
                result_queue.put({
                    'task_id': task['id'],
                    'result': result,
                    'success': True
                })

            except Exception as e:
                result_queue.put({
                    'task_id': task['id'],
                    'error': str(e),
                    'success': False
                })

    async def _collect_results(self, worker_id: int):
        """Collect results from worker"""
        worker = self.workers[worker_id]
        while not self._stop_event.is_set():
            try:
                if not worker['result_queue'].empty():
                    result = worker['result_queue'].get()
                    task_id = result['task_id']
                    self.results[task_id] = result
                    worker['busy'] = False

                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Result collection error: {str(e)}")
                await asyncio.sleep(1)

    async def _get_available_worker(self) -> Optional[int]:
        """Find available worker"""
        for worker_id, worker in self.workers.items():
            if not worker['busy']:
                return worker_id
        return None

    def get_pool_status(self) -> Dict[str, Any]:
        """Get pool status information"""
        return {
            'workers': len(self.workers),
            'max_workers': self.max_workers,
            'active_tasks': len(self.tasks),
            'pending_results': len(self.results),
            'worker_status': {
                worker_id: {'busy': worker['busy']}
                for worker_id, worker in self.workers.items()
            }
        } 