#!/bin/bash

# GenAI CloudOps - Docker Deployment Script
# This script manages Docker Compose deployments for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"development"}
ACTION=${2:-"up"}
VERSION=${3:-"latest"}

echo -e "${BLUE}=== GenAI CloudOps Deployment Script ===${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}Action: ${ACTION}${NC}"
echo -e "${YELLOW}Version: ${VERSION}${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker Compose is not installed. Please install Docker Compose and try again.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites check passed${NC}"
}

# Function to setup environment
setup_environment() {
    echo -e "${BLUE}Setting up environment...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${YELLOW}⚠ Created .env from .env.example. Please review and update the values.${NC}"
        else
            echo -e "${RED}✗ No .env file found and no .env.example to copy from.${NC}"
            exit 1
        fi
    fi
    
    # Set version in environment
    export IMAGE_VERSION=${VERSION}
    
    echo -e "${GREEN}✓ Environment setup completed${NC}"
}

# Function to deploy application
deploy() {
    local compose_file=""
    local compose_override=""
    
    # Determine compose file based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        compose_file="docker-compose.prod.yml"
    else
        compose_file="docker-compose.yml"
    fi
    
    if [ ! -f "$compose_file" ]; then
        echo -e "${RED}✗ Compose file $compose_file not found.${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Using compose file: ${compose_file}${NC}"
    
    case $ACTION in
        "up")
            echo -e "${BLUE}Starting services...${NC}"
            docker-compose -f "$compose_file" up -d
            ;;
        "down")
            echo -e "${BLUE}Stopping services...${NC}"
            docker-compose -f "$compose_file" down
            ;;
        "restart")
            echo -e "${BLUE}Restarting services...${NC}"
            docker-compose -f "$compose_file" restart
            ;;
        "logs")
            echo -e "${BLUE}Showing logs...${NC}"
            docker-compose -f "$compose_file" logs -f
            ;;
        "status")
            echo -e "${BLUE}Showing service status...${NC}"
            docker-compose -f "$compose_file" ps
            ;;
        "build")
            echo -e "${BLUE}Building and starting services...${NC}"
            docker-compose -f "$compose_file" up -d --build
            ;;
        "pull")
            echo -e "${BLUE}Pulling latest images...${NC}"
            docker-compose -f "$compose_file" pull
            ;;
        "clean")
            echo -e "${BLUE}Cleaning up...${NC}"
            docker-compose -f "$compose_file" down -v --remove-orphans
            docker system prune -f
            ;;
        *)
            echo -e "${RED}✗ Unknown action: $ACTION${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Function to show service health
show_health() {
    echo -e "${BLUE}=== Service Health Status ===${NC}"
    
    local compose_file=""
    if [ "$ENVIRONMENT" = "production" ]; then
        compose_file="docker-compose.prod.yml"
    else
        compose_file="docker-compose.yml"
    fi
    
    # Get container statuses
    docker-compose -f "$compose_file" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo -e "${BLUE}=== Container Health Checks ===${NC}"
    
    # Check health of each service
    for container in $(docker-compose -f "$compose_file" ps -q); do
        if [ ! -z "$container" ]; then
            local name=$(docker inspect --format='{{.Name}}' $container | sed 's/\///')
            local health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "no healthcheck")
            
            if [ "$health" = "healthy" ]; then
                echo -e "${GREEN}✓ $name: $health${NC}"
            elif [ "$health" = "unhealthy" ]; then
                echo -e "${RED}✗ $name: $health${NC}"
            else
                echo -e "${YELLOW}⚠ $name: $health${NC}"
            fi
        fi
    done
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [ENVIRONMENT] [ACTION] [VERSION]${NC}"
    echo ""
    echo -e "${YELLOW}ENVIRONMENT:${NC}"
    echo "  development (default) - Use docker-compose.yml"
    echo "  production           - Use docker-compose.prod.yml"
    echo ""
    echo -e "${YELLOW}ACTION:${NC}"
    echo "  up (default)  - Start services"
    echo "  down          - Stop services"
    echo "  restart       - Restart services"
    echo "  logs          - Show logs"
    echo "  status        - Show service status"
    echo "  build         - Build and start services"
    echo "  pull          - Pull latest images"
    echo "  clean         - Stop services and clean up"
    echo "  health        - Show health status"
    echo ""
    echo -e "${YELLOW}VERSION:${NC}"
    echo "  latest (default) - Use latest images"
    echo "  v1.0.0           - Use specific version"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo -e "${YELLOW}  $0                              # Start development environment${NC}"
    echo -e "${YELLOW}  $0 production up v1.0.0         # Start production with specific version${NC}"
    echo -e "${YELLOW}  $0 development logs             # Show development logs${NC}"
    echo -e "${YELLOW}  $0 production status            # Show production status${NC}"
}

# Main execution
main() {
    # Handle help
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        exit 0
    fi
    
    # Handle health check
    if [ "$ACTION" = "health" ]; then
        show_health
        exit 0
    fi
    
    # Run deployment
    check_prerequisites
    setup_environment
    deploy
    
    # Show final status
    if [ "$ACTION" = "up" ] || [ "$ACTION" = "build" ]; then
        echo ""
        show_health
    fi
    
    echo ""
    echo -e "${GREEN}✓ Deployment action '$ACTION' completed successfully!${NC}"
}

# Run main function
main "$@" 