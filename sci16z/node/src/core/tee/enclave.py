import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.logger import get_logger

class TEEEnclave:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.enclave_path = os.path.join(os.path.dirname(__file__), '../../data/enclave')
        self.measurements = {}
        self.encryption_key = None
        self.initialized = False

    async def initialize(self, seed: bytes) -> bool:
        """Initialize TEE enclave"""
        try:
            # Create secure storage
            os.makedirs(self.enclave_path, exist_ok=True)
            
            # Generate encryption key
            self.encryption_key = self._generate_key(seed)
            
            # Initialize measurements
            self.measurements = self._load_measurements()
            
            self.initialized = True
            self.logger.info("TEE enclave initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TEE enclave: {str(e)}")
            return False

    def _generate_key(self, seed: bytes) -> bytes:
        """Generate encryption key from seed"""
        try:
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(seed))
            
            # Save salt for key regeneration
            salt_path = os.path.join(self.enclave_path, '.salt')
            with open(salt_path, 'wb') as f:
                f.write(salt)
                
            return key
            
        except Exception as e:
            self.logger.error(f"Failed to generate encryption key: {str(e)}")
            raise

    def _load_measurements(self) -> Dict[str, str]:
        """Load integrity measurements"""
        measurement_path = os.path.join(self.enclave_path, 'measurements.json')
        if os.path.exists(measurement_path):
            try:
                with open(measurement_path, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_measurements(self):
        """Save integrity measurements"""
        try:
            measurement_path = os.path.join(self.enclave_path, 'measurements.json')
            with open(measurement_path, 'w') as f:
                json.dump(self.measurements, f)
        except Exception as e:
            self.logger.error(f"Failed to save measurements: {str(e)}")

    async def verify_measurement(self, path: str) -> bool:
        """Verify file integrity"""
        try:
            if not self.initialized:
                raise Exception("TEE enclave not initialized")
                
            if not os.path.exists(path):
                return False
                
            # Calculate current hash
            current_hash = self._calculate_hash(path)
            
            # Compare with stored measurement
            stored_hash = self.measurements.get(path)
            if not stored_hash:
                return False
                
            return current_hash == stored_hash
            
        except Exception as e:
            self.logger.error(f"Failed to verify measurement: {str(e)}")
            return False

    async def update_measurement(self, path: str) -> bool:
        """Update file integrity measurement"""
        try:
            if not self.initialized:
                raise Exception("TEE enclave not initialized")
                
            if not os.path.exists(path):
                return False
                
            # Calculate and store new hash
            self.measurements[path] = self._calculate_hash(path)
            self._save_measurements()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update measurement: {str(e)}")
            return False

    def _calculate_hash(self, path: str) -> str:
        """Calculate file hash"""
        try:
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash: {str(e)}")
            raise

    async def load_data(self, path: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt data"""
        try:
            if not self.initialized:
                raise Exception("TEE enclave not initialized")
                
            if not os.path.exists(path):
                return None
                
            with open(path, 'r') as f:
                encrypted_data = json.load(f)
                
            if not encrypted_data.get('encrypted', False):
                return encrypted_data
                
            # Decrypt data
            f = Fernet(self.encryption_key)
            decrypted = f.decrypt(encrypted_data['data'].encode())
            return json.loads(decrypted)
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {str(e)}")
            return None

    async def save_data(self, path: str, data: Dict[str, Any]) -> bool:
        """Encrypt and save data"""
        try:
            if not self.initialized:
                raise Exception("TEE enclave not initialized")
                
            # Encrypt data
            f = Fernet(self.encryption_key)
            encrypted = f.encrypt(json.dumps(data).encode())
            
            # Save encrypted data
            with open(path, 'w') as f:
                json.dump({
                    'encrypted': True,
                    'data': encrypted.decode(),
                    'timestamp': datetime.now().isoformat()
                }, f)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save data: {str(e)}")
            return False

    def get_report(self) -> Dict[str, Any]:
        """Get enclave status report"""
        return {
            'status': 'initialized' if self.initialized else 'not_initialized',
            'measurements': len(self.measurements),
            'timestamp': datetime.now().isoformat()
        } 