#!/bin/bash

# Langflow Installation Script
# This script automates the complete installation process for Langflow

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    else
        # Check Python version
        python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
            missing_deps+=("python3.8+")
        else
            log_success "Python $python_version found"
        fi
    fi
    
    if ! command_exists git; then
        missing_deps+=("git")
    else
        log_success "Git found"
    fi
    
    if ! command_exists node; then
        missing_deps+=("node")
    else
        log_success "Node.js found"
    fi
    
    if ! command_exists npm; then
        missing_deps+=("npm")
    else
        log_success "npm found"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again."
        
        # Provide installation hints based on the OS
        if command_exists apt-get; then
            log_info "On Ubuntu/Debian, you can install with:"
            log_info "sudo apt-get update && sudo apt-get install python3 python3-pip python3-venv git nodejs npm"
        elif command_exists yum; then
            log_info "On CentOS/RHEL, you can install with:"
            log_info "sudo yum install python3 python3-pip git nodejs npm"
        elif command_exists brew; then
            log_info "On macOS, you can install with:"
            log_info "brew install python3 git node npm"
        fi
        
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

# Make scripts executable
make_executable() {
    log_info "Making scripts executable..."
    chmod +x start.sh
    chmod +x setup.py
    chmod +x verify_setup.py
    log_success "Scripts are now executable"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Check if we need to install system packages
    if command_exists apt-get; then
        # Ubuntu/Debian
        log_info "Detected Debian/Ubuntu system"
        if ! dpkg -l | grep -q python3-dev; then
            log_info "Installing python3-dev..."
            sudo apt-get update
            sudo apt-get install -y python3-dev python3-venv build-essential
        fi
    elif command_exists yum; then
        # CentOS/RHEL
        log_info "Detected CentOS/RHEL system"
        if ! rpm -qa | grep -q python3-devel; then
            log_info "Installing python3-devel..."
            sudo yum install -y python3-devel gcc gcc-c++ make
        fi
    else
        log_warning "Could not detect package manager, skipping system dependencies"
    fi
}

# Run Python setup
run_python_setup() {
    log_info "Running Python setup script..."
    if python3 setup.py; then
        log_success "Python setup completed successfully"
    else
        log_error "Python setup failed"
        exit 1
    fi
}

# Create startup script
create_startup_script() {
    log_info "Creating startup configuration..."
    
    # Ensure start.sh is properly configured
    if [ ! -f "start.sh" ]; then
        log_error "start.sh not found"
        exit 1
    fi
    
    log_success "Startup script ready"
}

# Main installation function
main() {
    echo "🚀 Langflow Installation Script"
    echo "================================"
    
    # Run installation steps
    check_prerequisites
    make_executable
    install_system_deps
    run_python_setup
    create_startup_script
    
    echo ""
    echo "================================"
    log_success "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Run './start.sh' to start Langflow"
    echo "2. Run 'python3 verify_setup.py' to verify installation"
    echo "3. Open http://localhost:7860 in your browser"
    echo ""
    echo "For troubleshooting, check the README.md file"
}

# Trap errors and provide helpful message
trap 'log_error "Installation failed. Check the error messages above."' ERR

# Run main function
main "$@"
