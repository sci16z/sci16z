import os
import yaml
from typing import Dict, Any, Optional
from utils.logger import get_logger

class ConfigManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = {}
        self.config_path = os.path.join(os.path.dirname(__file__), '../config/config.yaml')
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.config, f)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set configuration value"""
        try:
            keys = key.split('.')
            target = self.config
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self.save_config()
        except Exception as e:
            self.logger.error(f"Failed to set configuration: {str(e)}")
            raise 