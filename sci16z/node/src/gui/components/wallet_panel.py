from __future__ import annotations
import asyncio
import gradio as gr
from typing import Dict, Any, Tuple, List
from utils.logger import get_logger
from utils.security import TEEManager

class WalletPanel:
    def __init__(self, tee_manager: TEEManager):
        self.logger = get_logger(__name__)
        self.tee_manager = tee_manager
        self.wallet_address = None
        self.balance = None
        self.rewards = None
        self.withdraw_amount = None
        self.withdraw_status = None

    def create_ui(self) -> gr.Column:
        """Create wallet panel UI"""
        with gr.Column() as panel:
            gr.Markdown("### Wallet Information")
            
            with gr.Row():
                with gr.Column(scale=2):
                    self.wallet_address = gr.Textbox(
                        label="Wallet Address",
                        placeholder="Please import wallet...",
                        interactive=False
                    )
                    self.balance = gr.Number(
                        label="Current Balance",
                        value=0.0,
                        interactive=False
                    )
                    
                with gr.Column(scale=1):
                    import_btn = gr.Button("Import Wallet")
                    export_btn = gr.Button("Export Wallet")
            
            gr.Markdown("### Reward History")
            self.rewards = gr.DataFrame(
                headers=["Time", "Task ID", "Reward Amount", "Status"],
                interactive=False
            )
            
            gr.Markdown("### Withdraw")
            with gr.Row():
                self.withdraw_amount = gr.Number(
                    label="Withdraw Amount",
                    value=0.0,
                    minimum=0.0,
                    interactive=True
                )
                withdraw_btn = gr.Button("Withdraw")
                
            self.withdraw_status = gr.Label(
                label="Withdraw Status",
                value="",
                visible=False
            )
            
            # 绑定事件
            import_btn.click(fn=self.import_wallet)
            export_btn.click(fn=self.export_wallet)
            withdraw_btn.click(
                fn=self.withdraw,
                inputs=[self.withdraw_amount],
                outputs=[self.withdraw_status, self.balance]
            )
            
        return panel

    async def load_wallet(self) -> bool:
        """加载钱包信息"""
        try:
            wallet_data = await self.tee_manager.secure_load('wallet.json')
            if wallet_data and self.wallet_address:
                self.wallet_address.update(value=wallet_data['address'])
                return True
            return False
        except Exception as e:
            self.logger.error(f"加载钱包失败: {str(e)}")
            return False

    def import_wallet(self) -> Dict[str, Any]:
        """导入钱包"""
        try:
            # TODO: 实现钱包导入逻辑
            # 1. 打开文件选择器
            # 2. 验证钱包文件
            # 3. 加密保存到TEE环境
            return {
                "success": True,
                "message": "钱包导入成功"
            }
        except Exception as e:
            self.logger.error(f"钱包导入失败: {str(e)}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }

    def export_wallet(self) -> Dict[str, Any]:
        """导出钱包"""
        try:
            # TODO: 实现钱包导出逻辑
            # 1. 从TEE环境解密钱包数据
            # 2. 保存到用户选择的位置
            return {
                "success": True,
                "message": "钱包导出成功"
            }
        except Exception as e:
            self.logger.error(f"钱包导出失败: {str(e)}")
            return {
                "success": False,
                "message": f"导出失败: {str(e)}"
            }

    async def update_balance(self) -> float:
        """更新余额"""
        try:
            # TODO: 从任务池获取最新余额
            balance = 0.0
            if self.balance:
                self.balance.update(value=balance)
            return balance
        except Exception as e:
            self.logger.error(f"更新余额失败: {str(e)}")
            return 0.0

    async def update_rewards(self) -> List[List[Any]]:
        """更新奖励记录"""
        try:
            # TODO: 从任务池获取奖励记录
            rewards = []
            if self.rewards:
                self.rewards.update(value=rewards)
            return rewards
        except Exception as e:
            self.logger.error(f"更新奖励记录失败: {str(e)}")
            return []

    async def withdraw(self, amount: float) -> Tuple[str, float]:
        """提现操作"""
        try:
            if amount <= 0:
                return "提现金额必须大于0", self.balance.value
                
            if amount > self.balance.value:
                return "余额不足", self.balance.value
                
            # TODO: 实现提现逻辑
            # 1. 调用任务池API
            # 2. 等待确认
            # 3. 更新余额
            
            new_balance = self.balance.value - amount
            self.balance.update(value=new_balance)
            
            return "提现申请已提交，等待处理", new_balance
            
        except Exception as e:
            self.logger.error(f"提现失败: {str(e)}")
            return f"提现失败: {str(e)}", self.balance.value

    def refresh(self):
        """刷新所有信息"""
        try:
            asyncio.create_task(self.load_wallet())
            asyncio.create_task(self.update_balance())
            asyncio.create_task(self.update_rewards())
        except Exception as e:
            self.logger.error(f"刷新失败: {str(e)}") 