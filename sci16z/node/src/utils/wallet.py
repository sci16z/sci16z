from __future__ import annotations
import json
import os
from pathlib import Path
import aiohttp
from typing import Dict, Any, Optional
from utils.logger import get_logger
from utils.config import server_config

class WalletManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.wallet_endpoint = server_config.get_endpoint('wallet')
        self.config_path = Path(__file__).parent.parent.parent / "config" / "wallet.json"
        self.config = self._load_config()
        self.balance = 0.0
        self.address = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load wallet configuration"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load wallet config: {str(e)}")
            return {}

    async def initialize(self, private_key: str) -> bool:
        """Initialize wallet"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.wallet_endpoint}/init",
                    json={
                        'private_key': private_key,
                        'network': self.config.get('network', 'mainnet')
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.address = data['address']
                        await self.update_balance()
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize wallet: {str(e)}")
            return False

    async def update_balance(self) -> float:
        """Update wallet balance"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.wallet_endpoint}/balance/{self.address}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.balance = float(data['balance'])
            return self.balance
        except Exception as e:
            self.logger.error(f"Failed to update balance: {str(e)}")
            return self.balance

    async def withdraw(self, amount: float) -> bool:
        """Withdraw funds"""
        try:
            if amount > self.balance:
                self.logger.warning("Insufficient balance for withdrawal")
                return False
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.wallet_endpoint}/withdraw",
                    json={
                        'address': self.address,
                        'amount': amount,
                        'gas_limit': self.config.get('gas_limit', 21000),
                        'gas_price': self.config.get('gas_price', 'auto')
                    }
                ) as response:
                    if response.status == 200:
                        await self.update_balance()
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to withdraw: {str(e)}")
            return False

    def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information"""
        return {
            'address': self.address,
            'balance': self.balance,
            'network': self.config.get('network', 'mainnet'),
            'auto_withdraw': self.config.get('auto_withdraw', True),
            'min_withdraw': self.config.get('min_withdraw', 1.0)
        } 