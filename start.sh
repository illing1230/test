#!/bin/bash

# Langflow Startup Script
# This script starts the Langflow development server

set -e

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

# Configuration
LANGFLOW_DIR="./langflow"
CONFIG_FILE="./langflow_config.yaml"
HOST="0.0.0.0"
PORT="5000"

# Check if langflow directory exists
check_installation() {
    if [ ! -d "$LANGFLOW_DIR" ]; then
        log_error "Langflow directory not found. Please run setup.py first."
        exit 1
    fi
    
    if [ ! -d "$LANGFLOW_DIR/venv" ]; then
        log_error "Virtual environment not found. Please run setup.py first."
        exit 1
    fi
    
    log_success "Installation found"
}

# Set up environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    # Database configuration from secrets
    if [ ! -z "$DATABASE_URL" ]; then
        export LANGFLOW_DATABASE_URL="$DATABASE_URL"
        log_info "Using DATABASE_URL from environment"
    elif [ ! -z "$PGHOST" ] && [ ! -z "$PGUSER" ] && [ ! -z "$PGPASSWORD" ] && [ ! -z "$PGDATABASE" ]; then
        export LANGFLOW_DATABASE_URL="postgresql://$PGUSER:$PGPASSWORD@$PGHOST:${PGPORT:-5432}/$PGDATABASE"
        log_info "Constructed PostgreSQL URL from environment variables"
    else
        log_info "Using default SQLite database"
        export LANGFLOW_DATABASE_URL="sqlite:///./langflow.db"
    fi
    
    # Set other environment variables
    export LANGFLOW_HOST="$HOST"
    export LANGFLOW_PORT="$PORT"
    export LANGFLOW_CONFIG_DIR="$(pwd)"
    
    # Development settings
    export LANGFLOW_LOG_LEVEL="INFO"
    export LANGFLOW_DEV_MODE="true"
    
    log_success "Environment configured"
}

# Activate virtual environment
activate_venv() {
    log_info "Activating virtual environment..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source "$LANGFLOW_DIR/venv/Scripts/activate"
    else
        # Unix-like systems
        source "$LANGFLOW_DIR/venv/bin/activate"
    fi
    
    log_success "Virtual environment activated"
}

# Check langflow installation
check_langflow() {
    log_info "Checking Langflow installation..."
    
    if ! python -c "import langflow" 2>/dev/null; then
        log_error "Langflow not properly installed. Please run setup.py again."
        exit 1
    fi
    
    log_success "Langflow installation verified"
}

# Start frontend development server (if needed)
start_frontend() {
    local frontend_dir="$LANGFLOW_DIR/src/frontend"
    
    # Check alternative frontend location
    if [ ! -d "$frontend_dir" ]; then
        frontend_dir="$LANGFLOW_DIR/frontend"
    fi
    
    if [ -d "$frontend_dir" ] && [ -f "$frontend_dir/package.json" ]; then
        log_info "Starting frontend development server..."
        
        cd "$frontend_dir"
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            log_info "Installing frontend dependencies..."
            npm install
        fi
        
        # Start frontend in background
        npm run dev &
        FRONTEND_PID=$!
        
        cd - > /dev/null
        log_success "Frontend server started (PID: $FRONTEND_PID)"
    else
        log_info "Frontend directory not found, using built-in frontend"
    fi
}

# Start langflow server
start_langflow() {
    log_info "Starting Langflow server..."
    
    cd "$LANGFLOW_DIR"
    
    # Use config file if it exists
    local config_args=""
    if [ -f "../$CONFIG_FILE" ]; then
        config_args="--config ../$CONFIG_FILE"
        log_info "Using configuration file: $CONFIG_FILE"
    fi
    
    log_info "Server will be available at: http://localhost:$PORT"
    log_info "Press Ctrl+C to stop the server"
    
    # Start langflow
    python -m langflow run \
        --host "$HOST" \
        --port "$PORT" \
        $config_args \
        --log-level INFO \
        --dev
}

# Cleanup function
cleanup() {
    log_info "Shutting down services..."
    
    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "Stopping frontend server..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Main function
main() {
    echo "🚀 Starting Langflow Development Server"
    echo "======================================"
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    # Run startup sequence
    check_installation
    setup_environment
    activate_venv
    check_langflow
    start_frontend
    start_langflow
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Langflow Startup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --port PORT    Set the port (default: 7860)"
        echo "  --host HOST    Set the host (default: 0.0.0.0)"
        echo ""
        echo "Environment variables:"
        echo "  DATABASE_URL   Database connection URL"
        echo "  PGHOST         PostgreSQL host"
        echo "  PGUSER         PostgreSQL user"
        echo "  PGPASSWORD     PostgreSQL password"
        echo "  PGDATABASE     PostgreSQL database name"
        echo "  PGPORT         PostgreSQL port (default: 5432)"
        exit 0
        ;;
    --port)
        if [ -z "$2" ]; then
            log_error "Port value required"
            exit 1
        fi
        PORT="$2"
        shift 2
        ;;
    --host)
        if [ -z "$2" ]; then
            log_error "Host value required"
            exit 1
        fi
        HOST="$2"
        shift 2
        ;;
    *)
        # No arguments or unknown argument, proceed with main
        ;;
esac

# Run main function
main "$@"
