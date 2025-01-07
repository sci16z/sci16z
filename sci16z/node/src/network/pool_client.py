import asyncio
import json
import websockets
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.security import TEEManager

class PoolClient:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.ws = None
        self.connected = False
        self.tee_manager = TEEManager()
        self.config = self._load_config()
        self.wallet = None
        self.heartbeat_task = None

    def _load_config(self) -> dict:
        """Load pool configuration"""
        import os
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)['pool']

    async def connect(self):
        """Connect to task pool"""
        try:
            # Load wallet info
            self.wallet = await self._load_wallet()
            
            # Establish WebSocket connection
            self.ws = await websockets.connect(self.config['url'])
            
            # Send authentication
            await self._authenticate()
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            
            self.connected = True
            self.logger.info("Connected to task pool")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to task pool: {str(e)}")
            raise

    async def _load_wallet(self) -> Dict[str, str]:
        """Load wallet information"""
        try:
            return await self.tee_manager.secure_load('wallet.json')
        except Exception as e:
            self.logger.error(f"Failed to load wallet: {str(e)}")
            raise

    async def _authenticate(self):
        """Send authentication to task pool"""
        auth_message = {
            'type': 'auth',
            'wallet_address': self.wallet['address'],
            'signature': self._sign_message('auth')
        }
        await self.ws.send(json.dumps(auth_message))
        response = await self.ws.recv()
        if not json.loads(response).get('success'):
            raise Exception("Authentication failed")

    async def _heartbeat(self):
        """Keep connection alive with heartbeat"""
        while True:
            try:
                if self.ws and self.connected:
                    await self.ws.send(json.dumps({
                        'type': 'heartbeat',
                        'wallet_address': self.wallet['address']
                    }))
                await asyncio.sleep(self.config['heartbeat_interval'])
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
                await self.reconnect()

    async def reconnect(self):
        """Reconnect to task pool"""
        self.connected = False
        if self.ws:
            await self.ws.close()
        await asyncio.sleep(5)  # Wait 5 seconds before retry
        await self.connect()

    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get next available task"""
        if not self.connected:
            return None
            
        try:
            request = {
                'type': 'get_task',
                'wallet_address': self.wallet['address']
            }
            await self.ws.send(json.dumps(request))
            response = await self.ws.recv()
            task_data = json.loads(response)
            
            if task_data.get('type') == 'task':
                return task_data['data']
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get task: {str(e)}")
            await self.reconnect()
            return None

    async def submit_result(self, task_id: str, result: Dict[str, Any]):
        """Submit task result"""
        if not self.connected:
            raise Exception("Not connected to task pool")
            
        try:
            submission = {
                'type': 'submit',
                'task_id': task_id,
                'wallet_address': self.wallet['address'],
                'result': result,
                'signature': self._sign_message(f'submit_{task_id}')
            }
            await self.ws.send(json.dumps(submission))
            response = await self.ws.recv()
            
            if not json.loads(response).get('success'):
                raise Exception("Result submission failed")
                
        except Exception as e:
            self.logger.error(f"Failed to submit result: {str(e)}")
            await self.reconnect()
            raise

    def _sign_message(self, message: str) -> str:
        """Sign message with wallet private key"""
        # TODO: Implement actual message signing
        return "signed_" + message

    async def close(self):
        """Close connection"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.ws:
            await self.ws.close()
        self.connected = False 