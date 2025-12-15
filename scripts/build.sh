#!/bin/bash

# GenAI CloudOps - Docker Build Script
# This script builds Docker images for both frontend and backend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERSION=${1:-"latest"}
ENVIRONMENT=${2:-"development"}
REGISTRY=${3:-""}
PUSH=${4:-"false"}

echo -e "${BLUE}=== GenAI CloudOps Docker Build Script ===${NC}"
echo -e "${YELLOW}Version: ${VERSION}${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"
echo -e "${YELLOW}Registry: ${REGISTRY:-"local"}${NC}"
echo -e "${YELLOW}Push to registry: ${PUSH}${NC}"
echo ""

# Function to build and tag images
build_image() {
    local service=$1
    local dockerfile=$2
    local context=$3
    local target=$4
    
    echo -e "${BLUE}Building ${service} image...${NC}"
    
    # Build command
    local build_cmd="docker build"
    build_cmd+=" -f ${context}/${dockerfile}"
    build_cmd+=" -t genai-cloudops-${service}:${VERSION}"
    build_cmd+=" -t genai-cloudops-${service}:latest"
    
    if [ ! -z "$target" ]; then
        build_cmd+=" --target ${target}"
    fi
    
    if [ ! -z "$REGISTRY" ]; then
        build_cmd+=" -t ${REGISTRY}/genai-cloudops-${service}:${VERSION}"
        build_cmd+=" -t ${REGISTRY}/genai-cloudops-${service}:latest"
    fi
    
    build_cmd+=" ${context}"
    
    echo -e "${YELLOW}Executing: ${build_cmd}${NC}"
    eval $build_cmd
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${service} image built successfully${NC}"
    else
        echo -e "${RED}✗ Failed to build ${service} image${NC}"
        exit 1
    fi
}

# Function to push images
push_image() {
    local service=$1
    
    if [ ! -z "$REGISTRY" ] && [ "$PUSH" = "true" ]; then
        echo -e "${BLUE}Pushing ${service} image to registry...${NC}"
        docker push "${REGISTRY}/genai-cloudops-${service}:${VERSION}"
        docker push "${REGISTRY}/genai-cloudops-${service}:latest"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ ${service} image pushed successfully${NC}"
        else
            echo -e "${RED}✗ Failed to push ${service} image${NC}"
            exit 1
        fi
    fi
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Determine Dockerfile and target based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    BACKEND_DOCKERFILE="Dockerfile"
    FRONTEND_DOCKERFILE="Dockerfile"
    TARGET="production"
else
    BACKEND_DOCKERFILE="Dockerfile.dev"
    FRONTEND_DOCKERFILE="Dockerfile.dev"
    TARGET=""
fi

# Build backend image
build_image "backend" "$BACKEND_DOCKERFILE" "./backend" "$TARGET"

# Build frontend image  
build_image "frontend" "$FRONTEND_DOCKERFILE" "./frontend" "$TARGET"

# Push images if requested
push_image "backend"
push_image "frontend"

# Show built images
echo ""
echo -e "${GREEN}=== Built Images ===${NC}"
docker images | grep genai-cloudops

echo ""
echo -e "${GREEN}✓ Build completed successfully!${NC}"

# Usage instructions
echo ""
echo -e "${BLUE}Usage examples:${NC}"
echo -e "${YELLOW}  ./scripts/build.sh                                    # Build latest development images${NC}"
echo -e "${YELLOW}  ./scripts/build.sh v1.0.0 production                  # Build production v1.0.0${NC}"
echo -e "${YELLOW}  ./scripts/build.sh v1.0.0 production myregistry.com true  # Build, tag and push to registry${NC}" 