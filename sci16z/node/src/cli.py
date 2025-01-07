import click
import yaml
import os
from getpass import getpass
from typing import Dict, Any
from utils.config import server_config

@click.group()
def cli():
    """Sci16Z Node Management CLI"""
    pass

@cli.command()
def setup():
    """Initial setup of the node"""
    config = {}
    
    # Wallet setup
    click.echo("\nWallet Configuration")
    click.echo("===================")
    private_key = getpass("Enter wallet private key: ")
    
    config['wallet'] = {
        'private_key': private_key,
        'auto_withdraw': click.confirm("Enable auto withdrawal?", default=True),
        'min_withdraw': click.prompt("Minimum withdrawal amount", default=1.0, type=float)
    }
    
    # Pool setup
    click.echo("\nPool Configuration")
    click.echo("=================")
    config['pool'] = {
        'url': click.prompt("Pool URL", default=server_config.get_url('pool')),
        'heartbeat_interval': click.prompt("Heartbeat interval (seconds)", default=30, type=int)
    }
    
    # System setup
    click.echo("\nSystem Configuration")
    click.echo("===================")
    config['system'] = {
        'max_memory': click.prompt("Maximum memory usage (GB)", default=8, type=int),
        'max_disk_usage': click.prompt("Maximum disk usage ratio", default=0.9, type=float),
        'auto_clean': click.confirm("Enable auto cleanup?", default=True),
        'log_level': click.prompt("Log level", default="INFO", 
                                type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
    }
    
    # Save configuration
    os.makedirs('sci16z/node/config', exist_ok=True)
    with open('sci16z/node/config/config.yaml', 'w') as f:
        yaml.dump(config, f)
    
    click.echo("\nConfiguration saved!")

@cli.command()
def start():
    """Start the node"""
    # Verify configuration
    if not os.path.exists('sci16z/node/config/config.yaml'):
        click.echo("Configuration not found. Please run setup first.")
        return
        
    # Start node
    os.environ['NODE_ENV'] = 'production'
    from main import main
    import asyncio
    asyncio.run(main())

@cli.command()
def status():
    """Check node status"""
    try:
        from utils.metrics_collector import MetricsCollector
        metrics = MetricsCollector()
        stats = metrics.get_database_stats()
        click.echo(f"\nMetrics Status:")
        click.echo(f"Total Records: {stats['total_records']}")
        click.echo(f"Database Size: {stats['database_size_mb']:.2f}MB")
        click.echo(f"Metric Types: {', '.join(stats['metric_types'])}")
    except Exception as e:
        click.echo(f"Error getting status: {str(e)}")

@cli.command()
def withdraw():
    """Withdraw earnings"""
    try:
        from utils.wallet import WalletManager
        wallet = WalletManager()
        info = wallet.get_wallet_info()
        
        if not info['address']:
            click.echo("Wallet not initialized")
            return
            
        click.echo(f"\nWallet Status:")
        click.echo(f"Address: {info['address']}")
        click.echo(f"Balance: {info['balance']}")
        
        if click.confirm("Do you want to withdraw?"):
            amount = click.prompt("Enter amount", type=float)
            import asyncio
            success = asyncio.run(wallet.withdraw(amount))
            if success:
                click.echo("Withdrawal successful!")
            else:
                click.echo("Withdrawal failed!")
    except Exception as e:
        click.echo(f"Error processing withdrawal: {str(e)}")

if __name__ == '__main__':
    cli() 