import os
import json
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from utils.logger import get_logger

class CacheManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.base_path = os.path.join(os.path.dirname(__file__), '../cache')
        self.cache_config = {
            'pdf': {
                'path': 'pdf',
                'max_size_mb': 1000,  # 1GB
                'max_age_days': 7
            },
            'models': {
                'path': 'models',
                'max_size_mb': 5000,  # 5GB
                'max_age_days': 30
            },
            'images': {
                'path': 'images',
                'max_size_mb': 500,  # 500MB
                'max_age_days': 3
            },
            'temp': {
                'path': 'temp',
                'max_size_mb': 200,  # 200MB
                'max_age_days': 1
            }
        }
        self._init_cache_dirs()

    def _init_cache_dirs(self):
        """Initialize cache directories"""
        try:
            for cache_type, config in self.cache_config.items():
                cache_path = os.path.join(self.base_path, config['path'])
                os.makedirs(cache_path, exist_ok=True)
                
            self.logger.info("Cache directories initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cache directories: {str(e)}")
            raise

    async def store(self, cache_type: str, key: str, data: bytes) -> Optional[str]:
        """Store data in cache"""
        try:
            if cache_type not in self.cache_config:
                raise ValueError(f"Invalid cache type: {cache_type}")
                
            # Check cache size limits
            if not await self._check_cache_size(cache_type):
                await self.cleanup(cache_type)
                
            # Generate cache path
            cache_path = os.path.join(
                self.base_path,
                self.cache_config[cache_type]['path'],
                key
            )
            
            # Store data
            with open(cache_path, 'wb') as f:
                f.write(data)
                
            # Store metadata
            self._store_metadata(cache_path, {
                'created_at': datetime.now().isoformat(),
                'size': len(data),
                'type': cache_type
            })
            
            return cache_path
            
        except Exception as e:
            self.logger.error(f"Failed to store cache data: {str(e)}")
            return None

    async def retrieve(self, cache_type: str, key: str) -> Optional[bytes]:
        """Retrieve data from cache"""
        try:
            cache_path = os.path.join(
                self.base_path,
                self.cache_config[cache_type]['path'],
                key
            )
            
            if not os.path.exists(cache_path):
                return None
                
            # Check if cache is expired
            metadata = self._get_metadata(cache_path)
            if metadata and self._is_expired(metadata, cache_type):
                os.remove(cache_path)
                return None
                
            # Read data
            with open(cache_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve cache data: {str(e)}")
            return None

    async def cleanup(self, cache_type: Optional[str] = None):
        """Clean up expired or excess cache files"""
        try:
            types_to_clean = [cache_type] if cache_type else self.cache_config.keys()
            
            for cache_type in types_to_clean:
                cache_path = os.path.join(
                    self.base_path,
                    self.cache_config[cache_type]['path']
                )
                
                # Get all files with metadata
                files = []
                for filename in os.listdir(cache_path):
                    file_path = os.path.join(cache_path, filename)
                    metadata = self._get_metadata(file_path)
                    if metadata:
                        files.append((file_path, metadata))
                
                # Remove expired files
                for file_path, metadata in files:
                    if self._is_expired(metadata, cache_type):
                        os.remove(file_path)
                        continue
                
                # Check size limits
                if not await self._check_cache_size(cache_type):
                    # Sort by creation time and remove oldest
                    files.sort(key=lambda x: x[1]['created_at'])
                    while not await self._check_cache_size(cache_type) and files:
                        file_path, _ = files.pop(0)
                        os.remove(file_path)
                        
        except Exception as e:
            self.logger.error(f"Failed to cleanup cache: {str(e)}")

    def _store_metadata(self, file_path: str, metadata: Dict[str, Any]):
        """Store file metadata"""
        try:
            metadata_path = f"{file_path}.meta"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            self.logger.error(f"Failed to store metadata: {str(e)}")

    def _get_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata"""
        try:
            metadata_path = f"{file_path}.meta"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def _is_expired(self, metadata: Dict[str, Any], cache_type: str) -> bool:
        """Check if cache entry is expired"""
        try:
            created_at = datetime.fromisoformat(metadata['created_at'])
            max_age = timedelta(days=self.cache_config[cache_type]['max_age_days'])
            return datetime.now() - created_at > max_age
        except Exception:
            return True

    async def _check_cache_size(self, cache_type: str) -> bool:
        """Check if cache size is within limits"""
        try:
            cache_path = os.path.join(
                self.base_path,
                self.cache_config[cache_type]['path']
            )
            
            total_size = sum(
                os.path.getsize(os.path.join(cache_path, f))
                for f in os.listdir(cache_path)
                if os.path.isfile(os.path.join(cache_path, f))
            )
            
            max_size = self.cache_config[cache_type]['max_size_mb'] * 1024 * 1024
            return total_size <= max_size
            
        except Exception as e:
            self.logger.error(f"Failed to check cache size: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {}
            for cache_type, config in self.cache_config.items():
                cache_path = os.path.join(self.base_path, config['path'])
                
                # Calculate size and file count
                total_size = 0
                file_count = 0
                for f in os.listdir(cache_path):
                    if os.path.isfile(os.path.join(cache_path, f)):
                        total_size += os.path.getsize(os.path.join(cache_path, f))
                        file_count += 1
                        
                stats[cache_type] = {
                    'size_mb': total_size / (1024 * 1024),
                    'file_count': file_count,
                    'max_size_mb': config['max_size_mb'],
                    'usage_percent': (total_size / (config['max_size_mb'] * 1024 * 1024)) * 100
                }
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {} 