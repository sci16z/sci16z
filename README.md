# Sci16Z Distributed Computing Node

Sci16Z is a distributed scientific computing platform consisting of three main components: Computing Node, Task Pool, and Frontend Service.

## System Requirements

- Python 3.9+
- CUDA 11.7+ (for GPU acceleration, optional)
- 8GB+ RAM
- 10GB+ available disk space

## Quick Start

### 0. One-Click Setup
```bash
# On Linux/Mac:
./scripts/setup.sh

# On Windows:
scripts\setup.bat

# Or use CLI tool
python sci16z/node/src/cli.py setup
```

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Computing Node

```bash
# Configure environment variables
export NODE_ENV=development  # or production
# Pool URL will be loaded from config/server.yaml

# Start node
python sci16z/node/src/main.py
```

Configuration files are located in `sci16z/node/config/`:
- `config.yaml`: Basic configuration
- `models.yaml`: Model configuration
- `security.yaml`: Security configuration

### 3. Start Task Pool

```bash
# Configure environment variables
export POOL_ENV=development
export POOL_PORT=8080
export DB_URL=sqlite:///pool.db

# Initialize database
python sci16z/pool/src/init_db.py

# Start task pool service
python sci16z/pool/src/main.py
```

Task pool configuration file is located at `sci16z/pool/config/config.yaml`

### 4. Start Frontend Service

```bash
# Install frontend dependencies
cd sci16z/frontend
npm install

# Start in development mode
npm run dev

# Build for production
npm run build
npm run start
```

Frontend configuration file is located at `sci16z/frontend/.env`

## Deployment Guide

### Docker Deployment

1. Build Images
```bash
# Build node image
docker build -t sci16z-node -f docker/node/Dockerfile .

# Build pool image
docker build -t sci16z-pool -f docker/pool/Dockerfile .

# Build frontend image
docker build -t sci16z-frontend -f docker/frontend/Dockerfile .
```

2. Start with docker-compose
```bash
docker-compose up -d
```

### Manual Deployment

1. Node Deployment
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-dev build-essential

# Install CUDA (optional)
# Follow NVIDIA official documentation

# Clone repository
git clone https://github.com/sci16z/sci16z.git
cd sci16z

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure service
sudo cp deploy/systemd/sci16z-node.service /etc/systemd/system/
sudo systemctl enable sci16z-node
sudo systemctl start sci16z-node
```

2. Pool Deployment
```bash
# Configure service
sudo cp deploy/systemd/sci16z-pool.service /etc/systemd/system/
sudo systemctl enable sci16z-pool
sudo systemctl start sci16z-pool
```

3. Frontend Deployment
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install -y nodejs

# Build frontend
cd sci16z/frontend
npm install
npm run build

# Configure Nginx
sudo cp deploy/nginx/sci16z.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx
```

## Debugging Guide

### Node Debugging

1. Enable debug logging
```bash
export LOG_LEVEL=DEBUG
```

2. Debug with VSCode
- Open project
- Select debug configuration "Python: Sci16Z Node"
- Press F5 to start debugging

### Pool Debugging

1. Enable debug mode
```bash
export POOL_DEBUG=true
```

2. Monitor database
```bash
python sci16z/pool/tools/monitor_db.py
```

### Frontend Debugging

1. Enable dev tools
```bash
# Set in .env
VITE_DEV_TOOLS=true
```

2. Use Chrome DevTools
- Open Chrome DevTools
- Switch to Network tab to monitor WebSocket connections
- Use Vue DevTools for component debugging

## Common Issues

1. Node Cannot Connect to Pool
- Check network connection
- Verify pool address configuration
- Check firewall settings

2. GPU Not Available
- Confirm CUDA installation
- Check GPU driver version
- Verify PyTorch CUDA version

3. High Memory Usage
- Adjust memory limits in `config.yaml`
- Check concurrent task settings
- Consider increasing system memory

## Additional Resources

- [Full Documentation](https://docs.sci16z.com)
- [API Documentation](https://api.sci16z.com)
- [Issue Tracker](https://github.com/your-org/sci16z/issues)
- [Contributing Guide](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE) for details
```

This README includes:
1. System requirements
2. Quick start guide
3. Detailed deployment steps
4. Debugging guide
5. Common issues and solutions
6. Additional resources
7. License information

All content is in English and formatted for better readability.
