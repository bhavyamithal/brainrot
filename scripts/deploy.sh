#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "All dependencies satisfied"
}

check_env_file() {
    if [ ! -f ".env" ]; then
        log_warning "No .env file found"
        if [ -f ".env.example" ]; then
            log_info "Copying .env.example to .env"
            cp .env.example .env
            log_warning "Please edit .env with your API credentials before running the pipeline"
        else
            log_error "No .env.example found. Please create .env manually."
            exit 1
        fi
    else
        log_success ".env file exists"
    fi
}

create_directories() {
    log_info "Creating required directories..."
    
    mkdir -p cache credentials output logs
    
    log_success "Directories created"
}

pull_latest() {
    if [ -d ".git" ]; then
        log_info "Pulling latest code..."
        git pull || log_warning "Could not pull latest code (continuing anyway)"
    else
        log_info "Not a git repository, skipping pull"
    fi
}

build_containers() {
    log_info "Building Docker containers..."
    
    if docker compose version &> /dev/null; then
        docker compose build
    else
        docker-compose build
    fi
    
    log_success "Containers built successfully"
}

start_services() {
    log_info "Starting services..."
    
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    log_success "Services started"
}

show_status() {
    log_info "Service status:"
    echo ""
    
    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi
    
    echo ""
    log_info "Logs can be viewed with:"
    echo "  docker compose logs -f scheduler"
    echo "  docker compose logs -f dashboard"
    echo ""
    log_info "Dashboard available at: http://localhost:8501"
}

stop_services() {
    log_info "Stopping services..."
    
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
    
    log_success "Services stopped"
}

show_logs() {
    local service="${1:-}"
    
    if [ -z "$service" ]; then
        if docker compose version &> /dev/null; then
            docker compose logs -f
        else
            docker-compose logs -f
        fi
    else
        if docker compose version &> /dev/null; then
            docker compose logs -f "$service"
        else
            docker-compose logs -f "$service"
        fi
    fi
}

restart_services() {
    stop_services
    start_services
}

show_help() {
    echo "Brainrot Deployment Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy    Build and start all services (default)"
    echo "  start     Start existing services"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  status    Show service status"
    echo "  logs      Show logs (optional: specify service name)"
    echo "  build     Build containers only"
    echo "  help      Show this help message"
}

main() {
    local command="${1:-deploy}"
    
    case "$command" in
        deploy)
            check_dependencies
            check_env_file
            create_directories
            pull_latest
            build_containers
            start_services
            show_status
            ;;
        start)
            check_dependencies
            start_services
            show_status
            ;;
        stop)
            stop_services
            ;;
        restart)
            check_dependencies
            restart_services
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        build)
            check_dependencies
            build_containers
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
