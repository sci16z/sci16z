import os
import sys
import platform
import subprocess
import venv
import yaml
import getpass
from pathlib import Path

class Setup:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        self.config_dir = self.project_root / "sci16z/node/config"

    def print_colored(self, text: str, color: str = "green"):
        """Print colored text (if supported)"""
        colors = {
            "green": "\033[0;32m",
            "yellow": "\033[1;33m",
            "red": "\033[0;31m",
            "reset": "\033[0m"
        }
        
        if self.os_type != "windows":
            print(f"{colors.get(color, '')}{text}{colors['reset']}")
        else:
            print(text)

    def create_venv(self):
        """Create virtual environment"""
        self.print_colored("\nCreating virtual environment...", "yellow")
        venv.create(self.venv_path, with_pip=True)

    def get_venv_python(self) -> str:
        """Get path to virtual environment python"""
        if self.os_type == "windows":
            return str(self.venv_path / "Scripts" / "python.exe")
        return str(self.venv_path / "bin" / "python")

    def install_dependencies(self):
        """Install dependencies"""
        self.print_colored("\nInstalling dependencies...", "yellow")
        requirements = self.project_root / "requirements.txt"
        subprocess.check_call([
            self.get_venv_python(),
            "-m", "pip", "install", "-r", str(requirements)
        ])

    def setup_config(self):
        """Setup configuration"""
        self.print_colored("\nSetting up configuration...", "yellow")
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Get wallet configuration
        wallet_key = getpass.getpass("Enter wallet private key: ")

        # Load server config for default pool URL
        server_config = yaml.safe_load((self.config_dir / "server.yaml").read_text())
        pool_url = server_config['servers']['pool']

        # Generate config
        config = {
            'wallet': {
                'private_key': wallet_key,
                'auto_withdraw': True,
                'min_withdraw': 1.0
            },
            'pool': {
                'url': pool_url,
                'heartbeat_interval': 30
            },
            'system': {
                'max_memory': 8,
                'max_disk_usage': 0.9,
                'auto_clean': True,
                'log_level': "INFO"
            }
        }

        # Save config
        with open(self.config_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)

    def create_startup_script(self):
        """Create startup script"""
        if self.os_type == "windows":
            script = self.project_root / "start_node.bat"
            content = f"""@echo off
call {self.venv_path}\\Scripts\\activate.bat
set NODE_ENV=production
python sci16z/node/src/main.py
"""
        else:
            script = self.project_root / "start_node.sh"
            content = f"""#!/bin/bash
source {self.venv_path}/bin/activate
export NODE_ENV=production
python sci16z/node/src/main.py
"""

        with open(script, "w") as f:
            f.write(content)

        if self.os_type != "windows":
            script.chmod(0o755)

    def run(self):
        """Run setup"""
        try:
            self.print_colored("Sci16Z Node Setup")
            self.print_colored("================")

            # Check Python version
            if sys.version_info < (3, 9):
                raise RuntimeError("Python 3.9+ is required")

            self.create_venv()
            self.install_dependencies()
            self.setup_config()
            self.create_startup_script()

            self.print_colored("\nSetup completed!", "green")
            if self.os_type == "windows":
                self.print_colored("To start the node, run: start_node.bat", "yellow")
            else:
                self.print_colored("To start the node, run: ./start_node.sh", "yellow")

        except Exception as e:
            self.print_colored(f"\nError: {str(e)}", "red")
            sys.exit(1)

if __name__ == "__main__":
    Setup().run() 