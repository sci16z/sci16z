from __future__ import annotations
import os
import hashlib
from typing import Dict, Any, Optional
from utils.logger import get_logger
from core.tee.enclave import TEEEnclave
from utils.config import server_config

class SecurityManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.enclave = TEEEnclave()
        self.initialized = False
        self.api_endpoint = server_config.get_url('api')

    async def initialize(self) -> bool:
        """Initialize security manager"""
        try:
            # Generate secure seed
            seed = os.urandom(32)
            
            # Initialize TEE enclave
            if await self.enclave.initialize(seed):
                self.initialized = True
                self.logger.info("Security manager initialized")
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize security manager: {str(e)}")
            return False

    async def verify_integrity(self, path: str) -> bool:
        """Verify file integrity"""
        try:
            if not self.initialized:
                raise Exception("Security manager not initialized")
                
            url = f"{self.api_endpoint}/v1/verify"
            return await self.enclave.verify_measurement(path)
            
        except Exception as e:
            self.logger.error(f"Failed to verify integrity: {str(e)}")
            return False

    async def secure_load(self, path: str) -> Optional[Dict[str, Any]]:
        """Load and verify secure data"""
        try:
            if not self.initialized:
                raise Exception("Security manager not initialized")
                
            # Verify file integrity
            if not await self.verify_integrity(path):
                raise Exception("Integrity check failed")
                
            # Load and decrypt data
            return await self.enclave.load_data(path)
            
        except Exception as e:
            self.logger.error(f"Failed to load secure data: {str(e)}")
            return None

    async def secure_save(self, path: str, data: Dict[str, Any]) -> bool:
        """Save data securely"""
        try:
            if not self.initialized:
                raise Exception("Security manager not initialized")
                
            # Encrypt and save data
            if await self.enclave.save_data(path, data):
                # Update integrity measurement
                return await self.enclave.update_measurement(path)
                
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to save secure data: {str(e)}")
            return False

    def get_security_report(self) -> Dict[str, Any]:
        """Get security status report"""
        try:
            if not self.initialized:
                return {
                    'status': 'not_initialized',
                    'measurements': {},
                    'timestamp': None
                }
                
            return self.enclave.get_report()
            
        except Exception as e:
            self.logger.error(f"Failed to get security report: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 