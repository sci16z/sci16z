import os
from pathlib import Path

required_dirs = [
    'sci16z/node/config',
    'sci16z/node/src/utils',
    'sci16z/node/src/network',
    'scripts'
]

required_files = [
    'sci16z/node/config/server.yaml',
    'sci16z/node/config/wallet.json',
    'sci16z/node/config/config.yaml',
    'sci16z/node/src/utils/wallet.py',
    'sci16z/node/src/utils/system_monitor.py',
    'sci16z/node/src/utils/task_status.py',
    'sci16z/node/src/network/pool_client.py',
    'sci16z/node/src/network/downloader.py',
    'sci16z/node/src/cli.py',
    'scripts/setup.sh'
]

def check_structure():
    # Check directories
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            print(f"Creating directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
    
    # Check files
    for file_path in required_files:
        if not os.path.isfile(file_path):
            print(f"Missing file: {file_path}")
            Path(file_path).touch()

if __name__ == "__main__":
    check_structure() 