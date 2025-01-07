#!/bin/bash

echo "Installing Sci16z Node..."

# Check system requirements
check_requirements() {
    echo "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is required but not installed."
        exit 1
    fi
    
    # Check CUDA (optional)
    if command -v nvidia-smi &> /dev/null; then
        echo "CUDA detected - GPU acceleration will be enabled"
    else
        echo "No CUDA detected - running in CPU mode"
    fi
}

# Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    
    # Create virtual environment
    python3 -m venv .sci16z-env
    source .sci16z-env/bin/activate
    
    # Install Python packages
    pip install --upgrade pip
    pip install torch torchvision torchaudio
    pip install transformers scipy numpy pandas
}

# Configure node
configure_node() {
    echo "Configuring Sci16z node..."
    
    # Create config directory
    mkdir -p ~/.sci16z/config
    
    # Generate node ID
    NODE_ID=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)
    
    # Create basic config
    cat > ~/.sci16z/config/node.env << EOF
NODE_ENV=production
NODE_ID=${NODE_ID}
POOL_URL=https://pool.sci16z.com
LOG_LEVEL=INFO
EOF
}

# Install service
install_service() {
    echo "Installing system service..."
    
    # Create service file
    cat > /tmp/sci16z-node.service << EOF
[Unit]
Description=Sci16z Computing Node
After=network.target

[Service]
Type=simple
User=$USER
Environment=NODE_ENV=production
WorkingDirectory=$HOME/.sci16z
ExecStart=$HOME/.sci16z-env/bin/python3 -m sci16z.node
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    # Install service
    sudo mv /tmp/sci16z-node.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable sci16z-node
}

# Main installation process
main() {
    echo "Starting Sci16z node installation..."
    
    check_requirements
    install_dependencies
    configure_node
    install_service
    
    echo "Installation complete!"
    echo "Node ID: ${NODE_ID}"
    echo "To start the node: sudo systemctl start sci16z-node"
    echo "To check status: sudo systemctl status sci16z-node"
}

main 