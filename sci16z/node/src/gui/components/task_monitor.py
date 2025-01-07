from __future__ import annotations
import gradio as gr
from datetime import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.task_status import TaskStatus

class TaskMonitor:
    def __init__(self, task_manager):
        self.logger = get_logger(__name__)
        self.task_manager = task_manager
        self.task_list = None
        self.task_detail = None
        self.auto_refresh = False
        self.refresh_interval = 5  # seconds

    def create_ui(self) -> gr.Column:
        """Create task monitor UI"""
        with gr.Column() as monitor:
            gr.Markdown("### Task Monitor")
            
            with gr.Row():
                with gr.Column(scale=2):
                    self.task_list = gr.DataFrame(
                        headers=["Task ID", "Status", "Progress", "Start Time", "Update Time"],
                        interactive=False
                    )
                
                with gr.Column(scale=1):
                    self.task_detail = gr.JSON(
                        label="Task Details",
                        value={}
                    )
            
            with gr.Row():
                refresh_btn = gr.Button("Refresh")
                auto_refresh = gr.Checkbox(
                    label="Auto Refresh",
                    value=False
                )
                clear_btn = gr.Button("Clear History")
            
            refresh_btn.click(fn=self.refresh_tasks)
            auto_refresh.change(fn=self.toggle_auto_refresh)
            clear_btn.click(fn=self.clear_history)
            
            # Task list click event
            self.task_list.select(fn=self.show_task_detail)
            
        return monitor

    def refresh_tasks(self) -> List[List[Any]]:
        """Refresh task list"""
        try:
            active_tasks = self.task_manager.get_active_tasks()
            recent_history = self.task_manager.get_task_history(limit=10)
            
            # Merge active tasks and recent history
            all_tasks = []
            
            for task_id, task in active_tasks.items():
                all_tasks.append([
                    task_id,
                    task['status'].value,
                    f"{task['progress']}%",
                    task['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                    task['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                ])
            
            for task_id, task in recent_history.items():
                all_tasks.append([
                    task_id,
                    task['status'].value,
                    "100%" if task['status'] == TaskStatus.COMPLETED else "Failed",
                    task['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                    task['completed_at'].strftime("%Y-%m-%d %H:%M:%S") if 'completed_at' in task
                    else task['failed_at'].strftime("%Y-%m-%d %H:%M:%S")
                ])
            
            if self.task_list:
                self.task_list.update(value=all_tasks)
            return all_tasks
            
        except Exception as e:
            self.logger.error(f"Failed to refresh task list: {str(e)}")
            return []

    def show_task_detail(self, evt: gr.SelectData) -> Dict[str, Any]:
        """Show task details"""
        try:
            task_id = evt.value[0]  # Get selected task ID
            task = self.task_manager.get_task_status(task_id)
            
            if task and self.task_detail:
                self.task_detail.update(value=task)
                return task
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to show task details: {str(e)}")
            return {}

    def toggle_auto_refresh(self, enabled: bool):
        """Toggle auto refresh"""
        self.auto_refresh = enabled
        if enabled:
            gr.set_interval(self.refresh_tasks, interval=self.refresh_interval)

    def clear_history(self):
        """Clear task history"""
        try:
            self.task_manager.cleanup_old_history()
            self.refresh_tasks()
        except Exception as e:
            self.logger.error(f"Failed to clear history: {str(e)}") 