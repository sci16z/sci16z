from __future__ import annotations
import os
import aiohttp
import asyncio
from typing import Optional
from utils.logger import get_logger
from utils.config import server_config

class ModelDownloader:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.model_endpoint = server_config.get_endpoint('model_download')
        self.download_path = os.path.join(os.path.dirname(__file__), '../models')
        os.makedirs(self.download_path, exist_ok=True)

    async def download_model(self, model_id: str) -> Optional[str]:
        """Download model files"""
        try:
            model_path = os.path.join(self.download_path, model_id)
            if os.path.exists(model_path):
                self.logger.info(f"Model {model_id} already exists")
                return model_path

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.model_endpoint}/{model_id}"
                ) as response:
                    if response.status == 200:
                        with open(model_path, 'wb') as f:
                            while True:
                                chunk = await response.content.read(8192)
                                if not chunk:
                                    break
                                f.write(chunk)
                        return model_path
            return None
        except Exception as e:
            self.logger.error(f"Failed to download model: {str(e)}")
            return None

    async def check_updates(self) -> bool:
        """Check for model updates"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.model_endpoint}/updates"
                ) as response:
                    if response.status == 200:
                        updates = await response.json()
                        for model_id in updates:
                            await self.download_model(model_id)
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to check updates: {str(e)}")
            return False 