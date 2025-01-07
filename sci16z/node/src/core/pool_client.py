from __future__ import annotations
import asyncio
import json
import websockets
from typing import Dict, Any, Optional, Callable
from utils.logger import get_logger
from utils.config import server_config
from utils.system_monitor import SystemMonitor

class PoolClient:
    def __init__(self, system_monitor: SystemMonitor):
        self.logger = get_logger(__name__)
        self.pool_url = server_config.get_endpoint('task_pool')
        self.system_monitor = system_monitor
        self.ws = None
        self.connected = False
        self.task_callback = None

    async def connect(self) -> bool:
        """Connect to task pool"""
        try:
            self.ws = await websockets.connect(self.pool_url)
            self.connected = True
            
            # Start heartbeat
            asyncio.create_task(self._heartbeat())
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
            self.logger.info(f"Connected to pool: {self.pool_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to pool: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from task pool"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            self.ws = None

    def register_task_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for new tasks"""
        self.task_callback = callback

    async def submit_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """Submit task result"""
        try:
            if not self.connected:
                raise Exception("Not connected to pool")
                
            message = {
                'type': 'result',
                'task_id': task_id,
                'result': result
            }
            await self.ws.send(json.dumps(message))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit result: {str(e)}")
            return False

    async def _heartbeat(self):
        """Send periodic heartbeat"""
        while self.connected:
            try:
                system_info = self.system_monitor.get_system_status()
                message = {
                    'type': 'heartbeat',
                    'system_info': system_info
                }
                await self.ws.send(json.dumps(message))
                await asyncio.sleep(30)  # 30 seconds interval
                
            except Exception as e:
                self.logger.error(f"Heartbeat error: {str(e)}")
                await asyncio.sleep(5)

    async def _handle_messages(self):
        """Handle incoming messages"""
        while self.connected:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if data['type'] == 'task' and self.task_callback:
                    await self.task_callback(data['task'])
                    
            except Exception as e:
                self.logger.error(f"Message handling error: {str(e)}")
                await asyncio.sleep(1) 