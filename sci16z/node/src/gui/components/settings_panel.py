from __future__ import annotations
import gradio as gr
from typing import Dict, Any
from utils.logger import get_logger
from utils.config_manager import ConfigManager
from utils.system_monitor import SystemMonitor

class SettingsPanel:
    def __init__(self, config_manager: ConfigManager, system_monitor: SystemMonitor):
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.system_monitor = system_monitor
        
        # UI components
        self.pool_url = None
        self.heartbeat_interval = None
        self.model_name = None
        self.gpu_enabled = None
        self.max_memory = None
        self.batch_size = None
        self.cache_dir = None
        self.log_level = None
        self.auto_clean = None
        
    def create_ui(self) -> gr.Column:
        """Create settings panel UI"""
        with gr.Column() as panel:
            with gr.Tab("Network Settings"):
                self.pool_url = gr.Textbox(
                    label="Task Pool URL",
                    value=self.config_manager.get("pool.url", ""),
                    placeholder="ws://pool.sci16z.com"
                )
                self.heartbeat_interval = gr.Number(
                    label="Heartbeat Interval (seconds)",
                    value=self.config_manager.get("pool.heartbeat_interval", 30),
                    minimum=5,
                    maximum=300
                )
                
            with gr.Tab("Model Settings"):
                self.model_name = gr.Dropdown(
                    label="Model Selection",
                    choices=self._get_available_models(),
                    value=self.config_manager.get("model.default")
                )
                self.gpu_enabled = gr.Checkbox(
                    label="Enable GPU",
                    value=self.config_manager.get("model.gpu_enabled", True)
                )
                self.max_memory = gr.Slider(
                    label="Max Memory Usage (GB)",
                    minimum=1,
                    maximum=24,
                    value=self.config_manager.get("model.max_memory", 8),
                    step=1
                )
                self.batch_size = gr.Number(
                    label="Batch Size",
                    value=self.config_manager.get("model.batch_size", 1),
                    minimum=1
                )
                
            with gr.Tab("System Settings"):
                self.cache_dir = gr.Textbox(
                    label="Cache Directory",
                    value=self.config_manager.get("system.cache_dir", "./cache")
                )
                self.log_level = gr.Dropdown(
                    label="Log Level",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    value=self.config_manager.get("system.log_level", "INFO")
                )
                self.auto_clean = gr.Checkbox(
                    label="Auto Clean Cache",
                    value=self.config_manager.get("system.auto_clean", True)
                )
                
                system_info = gr.JSON(
                    label="System Information",
                    value=self.system_monitor.get_system_info()
                )
                
            with gr.Row():
                save_btn = gr.Button("Save Settings")
                reset_btn = gr.Button("Reset")
                test_btn = gr.Button("Test Connection")
                
            # Status display
            self.status_label = gr.Label(
                label="Status",
                value="",
                visible=False
            )
            
            # Bind events
            save_btn.click(fn=self.save_settings)
            reset_btn.click(fn=self.reset_settings)
            test_btn.click(fn=self.test_connection)
            
        return panel

    def _get_available_models(self) -> list:
        """Get available model list"""
        try:
            models = self.config_manager.get("models", {})
            return list(models.keys())
        except Exception as e:
            self.logger.error(f"Failed to get model list: {str(e)}")
            return []

    def save_settings(self) -> Dict[str, Any]:
        """Save settings"""
        try:
            # Network settings
            self.config_manager.set("pool.url", self.pool_url.value)
            self.config_manager.set("pool.heartbeat_interval", self.heartbeat_interval.value)
            
            # Model settings
            self.config_manager.set("model.default", self.model_name.value)
            self.config_manager.set("model.gpu_enabled", self.gpu_enabled.value)
            self.config_manager.set("model.max_memory", self.max_memory.value)
            self.config_manager.set("model.batch_size", self.batch_size.value)
            
            # System settings
            self.config_manager.set("system.cache_dir", self.cache_dir.value)
            self.config_manager.set("system.log_level", self.log_level.value)
            self.config_manager.set("system.auto_clean", self.auto_clean.value)
            
            return {
                "success": True,
                "message": "Settings saved"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {str(e)}")
            return {
                "success": False,
                "message": f"Save failed: {str(e)}"
            }

    def reset_settings(self) -> Dict[str, Any]:
        """Reset settings"""
        try:
            # Reload configuration
            self.config_manager.load_config()
            
            # Update UI
            self.pool_url.update(value=self.config_manager.get("pool.url", ""))
            self.heartbeat_interval.update(value=self.config_manager.get("pool.heartbeat_interval", 30))
            self.model_name.update(value=self.config_manager.get("model.default"))
            self.gpu_enabled.update(value=self.config_manager.get("model.gpu_enabled", True))
            self.max_memory.update(value=self.config_manager.get("model.max_memory", 8))
            self.batch_size.update(value=self.config_manager.get("model.batch_size", 1))
            self.cache_dir.update(value=self.config_manager.get("system.cache_dir", "./cache"))
            self.log_level.update(value=self.config_manager.get("system.log_level", "INFO"))
            self.auto_clean.update(value=self.config_manager.get("system.auto_clean", True))
            
            return {
                "success": True,
                "message": "Settings reset"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {str(e)}")
            return {
                "success": False,
                "message": f"Reset failed: {str(e)}"
            }

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection"""
        try:
            import websockets
            import asyncio
            
            # Test WebSocket connection
            async with websockets.connect(self.pool_url.value) as ws:
                await ws.send('{"type": "ping"}')
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                
                if response:
                    return {
                        "success": True,
                        "message": "Connection test successful"
                    }
                    
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            } 