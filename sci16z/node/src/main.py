import asyncio
from utils.system_monitor import SystemMonitor
from utils.logger import get_logger
from utils.config import server_config
from utils.wallet import WalletManager
from core.task_processor import TaskProcessor
from core.pool_client import PoolClient

async def main():
    logger = get_logger(__name__)
    
    try:
        # 初始化系统监控
        system_monitor = SystemMonitor()
        
        # 初始化钱包
        wallet_manager = WalletManager()
        
        # 初始化任务处理器
        task_processor = TaskProcessor(wallet_manager)
        
        # 初始化任务池客户端
        pool_client = PoolClient(system_monitor)
        pool_client.register_task_callback(task_processor.process_task)
        
        # 连接到任务池
        if not await pool_client.connect():
            raise Exception("Failed to connect to task pool")
        
        # 记录服务器信息
        logger.info(f"Connected to pool server: {server_config.get_url('pool')}")
        logger.info(f"API endpoint: {server_config.get_url('api')}")
        
        # 保持程序运行
        while True:
            status = task_processor.get_running_tasks()
            logger.info(f"Pool status: {status}")
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await pool_client.disconnect()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 