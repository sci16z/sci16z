import os
import aiohttp
import aiofiles
from typing import Optional
from utils.logger import get_logger

class Downloader:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.session = None
        
    async def initialize(self):
        """Initialize downloader"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def download_file(self, url: str, save_path: str, chunk_size: int = 8192) -> Optional[str]:
        """Download file to specified path"""
        if not self.session:
            await self.initialize()
            
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Download failed: HTTP {response.status}")
                    
                # Ensure target directory exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # Download large files in chunks
                async with aiofiles.open(save_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        
                return save_path
                
        except Exception as e:
            self.logger.error(f"Failed to download file {url}: {str(e)}")
            if os.path.exists(save_path):
                os.remove(save_path)  # Clean up failed download
            return None

    async def close(self):
        """Close downloader"""
        if self.session:
            await self.session.close()
            self.session = None 