import gradio as gr
from typing import Optional
from utils.logger import get_logger
from gui.components.status_panel import StatusPanel
from gui.components.task_monitor import TaskMonitor
from gui.components.wallet_panel import WalletPanel
from gui.components.settings_panel import SettingsPanel

class GUIApp:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.app = None
        self.components = {}
        
    def initialize(self, **kwargs):
        """Initialize GUI components"""
        try:
            # Create component instances
            self.components['status'] = StatusPanel()
            self.components['tasks'] = TaskMonitor(kwargs['task_manager'])
            self.components['wallet'] = WalletPanel(kwargs['tee_manager'])
            self.components['settings'] = SettingsPanel(
                kwargs['config_manager'],
                kwargs['system_monitor']
            )
            
            self.logger.info("GUI components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GUI: {str(e)}")
            raise

    async def start(self):
        """Start GUI application"""
        try:
            with gr.Blocks(title="Sci16Z Node") as self.app:
                gr.Markdown("# Sci16Z Node Console")
                
                with gr.Tabs():
                    with gr.Tab("Status"):
                        self.components['status'].create_ui()
                        
                    with gr.Tab("Tasks"):
                        self.components['tasks'].create_ui()
                        
                    with gr.Tab("Wallet"):
                        self.components['wallet'].create_ui()
                        
                    with gr.Tab("Settings"):
                        self.components['settings'].create_ui()
                
            # Launch app
            self.app.queue()
            await self.app.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False
            )
            
        except Exception as e:
            self.logger.error(f"Failed to start GUI: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown GUI application"""
        if self.app:
            await self.app.close()
            self.app = None
            self.logger.info("GUI closed")

    def update_status(self, status: str):
        """Update status display"""
        if 'status' in self.components:
            self.components['status'].update_status(status)

    def update_task_list(self):
        """Update task list"""
        if 'tasks' in self.components:
            self.components['tasks'].refresh_tasks()

    def update_wallet_info(self):
        """Update wallet information"""
        if 'wallet' in self.components:
            self.components['wallet'].refresh() 