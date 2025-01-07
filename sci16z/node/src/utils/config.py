import os
import yaml
from typing import Dict, Any

class ServerConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = self._load_config()
            self.initialized = True
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = os.path.join(
            os.path.dirname(__file__), 
            '../config/server.yaml'
        )
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Failed to load server config: {e}")
            return {}
    
    def get_url(self, server_type: str) -> str:
        return self.config.get('servers', {}).get(server_type, '')
    
    def get_endpoint(self, endpoint_name: str) -> str:
        endpoint = self.config.get('endpoints', {}).get(endpoint_name, '')
        if endpoint:
            return endpoint.format(**self.config['servers'])
        return ''

server_config = ServerConfig() 