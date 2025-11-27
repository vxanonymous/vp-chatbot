#!/bin/bash

# Production Deployment Script for Vacation Planning System
# This script handles the complete production deployment process
# 
# NOTE: This script is designed for macOS systems only.
# For other operating systems, please adapt the commands accordingly.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
   exit 1
fi

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"

# Required environment variables
REQUIRED_VARS=(
    "OPENAI_API_KEY"
    "SECRET_KEY"
    "MONGODB_URL"
)

# Function to validate environment variables
validate_env() {
    log "Validating environment variables..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    missing_vars=()
    for var in "${REQUIRED_VARS[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
    
    success "Environment validation passed"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Function to backup existing deployment
backup_existing() {
    log "Creating backup of existing deployment..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        warning "Existing containers are running. Creating backup..."
        
        # Create backup directory
        BACKUP_DIR="$PROJECT_ROOT/backup/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup environment file
        if [[ -f "$ENV_FILE" ]]; then
            cp "$ENV_FILE" "$BACKUP_DIR/"
        fi
        
        # Backup MongoDB data (if exists)
        if docker volume ls | grep -q "vp-chatbot_mongodb-data"; then
            docker run --rm -v "vp-chatbot_mongodb-data:/data" -v "$BACKUP_DIR:/backup" \
                alpine tar czf /backup/mongodb-backup.tar.gz -C /data .
        fi
        
        success "Backup created in: $BACKUP_DIR"
    fi
}

# Function to stop existing containers
stop_containers() {
    log "Stopping existing containers..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        success "Existing containers stopped"
    else
        log "No running containers found"
    fi
}

# Function to build and start services
deploy_services() {
    log "Building and starting services..."
    
    # Build images
    log "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # Start services
    log "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    success "Services deployed successfully"
}

# Function to wait for services to be healthy
wait_for_health() {
    log "Waiting for services to be healthy..."
    
    services=("backend" "frontend" "mongodb")
    max_attempts=30
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        all_healthy=true
        
        for service in "${services[@]}"; do
            if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "healthy"; then
                all_healthy=false
                break
            fi
        done
        
        if [[ "$all_healthy" == true ]]; then
            success "All services are healthy"
            return 0
        fi
        
        log "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error "Services failed to become healthy within expected time"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs
    exit 1
}

# Function to run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Check backend health
    if curl -f http://localhost:8000/api/v1/health &> /dev/null; then
        success "Backend health check passed"
    else
        error "Backend health check failed"
        exit 1
    fi
    
    # Check frontend health
    if curl -f http://localhost &> /dev/null; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
        exit 1
    fi
    
    success "All health checks passed"
}

# Function to display deployment info
display_info() {
    log "Deployment completed successfully!"
    echo
    echo "Application URLs:"
    echo "  Frontend: http://localhost"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo
    echo "Useful commands:"
    echo "  View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "  Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
    echo
}

# Main deployment function
main() {
    log "Starting production deployment..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run deployment steps
    check_prerequisites
    validate_env
    backup_existing
    stop_containers
    deploy_services
    wait_for_health
    run_health_checks
    display_info
    
    success "Production deployment completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --validate    Only validate environment and prerequisites"
        echo
        echo "This script deploys the vacation planning system to production."
        exit 0
        ;;
    --validate)
        check_prerequisites
        validate_env
        success "Validation completed successfully"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac 