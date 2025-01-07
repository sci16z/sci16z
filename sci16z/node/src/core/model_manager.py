from __future__ import annotations
import os
from typing import Optional
import yaml
from langchain.llms import Ollama
from utils.logger import get_logger
from utils.gpu_monitor import GPUMonitor
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class ModelManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.model = None
        self.tokenizer = None
        self.config = self._load_config()
        self.device = self._setup_device()

    def _load_config(self) -> dict:
        """Load model configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '../config/models.yaml')
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load model config: {str(e)}")
            raise

    def _setup_device(self) -> str:
        """Setup compute device"""
        if torch.cuda.is_available() and self.config.get('use_gpu', True):
            return "cuda"
        return "cpu"

    async def load_model(self):
        """Load AI model"""
        try:
            model_name = self.config['default_model']
            model_config = self.config['models'][model_name]
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_config['path'])
            self.model = AutoModelForCausalLM.from_pretrained(
                model_config['path'],
                device_map=self.device,
                torch_dtype=torch.float16
            )
            
            self.logger.info(f"Model {model_name} loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            raise

    async def unload(self):
        """Unload model"""
        try:
            if self.model:
                del self.model
                self.model = None
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            torch.cuda.empty_cache()
            self.logger.info("Model unloaded")
        except Exception as e:
            self.logger.error(f"Failed to unload model: {str(e)}") 