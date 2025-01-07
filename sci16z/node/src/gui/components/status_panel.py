import gradio as gr
from typing import Dict, Any
from utils.logger import get_logger

class StatusPanel:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.connection_status = None
        self.task_status = None
        self.gpu_status = None
        self.system_status = None

    def create_ui(self) -> gr.Column:
        """Create status panel UI"""
        with gr.Column() as panel:
            gr.Markdown("### System Status")
            
            with gr.Row():
                with gr.Column(scale=1):
                    self.connection_status = gr.Label(
                        value="Not Connected",
                        label="Connection Status"
                    )
                    self.task_status = gr.Label(
                        value="Idle",
                        label="Task Status"
                    )
                
                with gr.Column(scale=1):
                    self.gpu_status = gr.Label(
                        value="Detecting...",
                        label="GPU Status"
                    )
                    self.system_status = gr.Label(
                        value="Normal",
                        label="System Status"
                    )
            
            with gr.Row():
                refresh_btn = gr.Button("Refresh Status")
                refresh_btn.click(fn=self.refresh_status)
                
        return panel

    def update_connection_status(self, status: str, color: str = None):
        """Update connection status"""
        if self.connection_status:
            self.connection_status.update(value=status)
            if color:
                self.connection_status.update(style={'color': color})

    def update_task_status(self, status: str, color: str = None):
        """Update task status"""
        if self.task_status:
            self.task_status.update(value=status)
            if color:
                self.task_status.update(style={'color': color})

    def update_gpu_status(self, info: Dict[str, Any]):
        """Update GPU status"""
        if self.gpu_status:
            if info['available']:
                status = f"Available ({info['backend']})"
                color = "green"
            else:
                status = "Not Available"
                color = "red"
            self.gpu_status.update(value=status, style={'color': color})

    def update_system_status(self, info: Dict[str, Any]):
        """Update system status"""
        if self.system_status:
            if info.get('healthy', True):
                status = "Normal"
                color = "green"
            else:
                status = f"Error: {info.get('error', 'Unknown error')}"
                color = "red"
            self.system_status.update(value=status, style={'color': color})

    def refresh_status(self):
        """Refresh all status"""
        try:
            # TODO: Get real-time status from components
            pass
        except Exception as e:
            self.logger.error(f"Failed to refresh status: {str(e)}") 