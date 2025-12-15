# GenAI CloudOps - Docker Deployment Script (PowerShell)
# This script manages Docker Compose deployments for different environments

param(
    [string]$Environment = "development",
    [string]$Action = "up",
    [string]$Version = "latest"
)

# Colors for output
$Red = [ConsoleColor]::Red
$Green = [ConsoleColor]::Green
$Yellow = [ConsoleColor]::Yellow
$Blue = [ConsoleColor]::Blue
$White = [ConsoleColor]::White

function Write-ColorOutput {
    param(
        [string]$Message,
        [ConsoleColor]$Color = $White
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "=== GenAI CloudOps Deployment Script ===" $Blue
Write-ColorOutput "Environment: $Environment" $Yellow
Write-ColorOutput "Action: $Action" $Yellow
Write-ColorOutput "Version: $Version" $Yellow
Write-Host ""

# Function to check prerequisites
function Test-Prerequisites {
    Write-ColorOutput "Checking prerequisites..." $Blue
    
    # Check if Docker is running
    try {
        & docker info | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker command failed"
        }
    }
    catch {
        Write-ColorOutput "X Docker is not running. Please start Docker and try again." $Red
        exit 1
    }
    
    # Check if Docker Compose is available
    try {
        & docker-compose --version | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker Compose command failed"
        }
    }
    catch {
        Write-ColorOutput "X Docker Compose is not installed. Please install Docker Compose and try again." $Red
        exit 1
    }
    
    Write-ColorOutput "√ Prerequisites check passed" $Green
}

# Function to setup environment
function Initialize-Environment {
    Write-ColorOutput "Setting up environment..." $Blue
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-ColorOutput "! Created .env from .env.example. Please review and update the values." $Yellow
        } else {
            Write-ColorOutput "X No .env file found and no .env.example to copy from." $Red
            exit 1
        }
    }
    
    # Set version in environment
    $env:IMAGE_VERSION = $Version
    
    Write-ColorOutput "√ Environment setup completed" $Green
}

# Function to deploy application
function Invoke-Deploy {
    $composeFile = ""
    
    # Determine compose file based on environment
    if ($Environment -eq "production") {
        $composeFile = "docker-compose.prod.yml"
    } else {
        $composeFile = "docker-compose.yml"
    }
    
    if (-not (Test-Path $composeFile)) {
        Write-ColorOutput "X Compose file $composeFile not found." $Red
        exit 1
    }
    
    Write-ColorOutput "Using compose file: $composeFile" $Blue
    
    try {
        switch ($Action) {
            "up" {
                Write-ColorOutput "Starting services..." $Blue
                & docker-compose -f $composeFile up -d
            }
            "down" {
                Write-ColorOutput "Stopping services..." $Blue
                & docker-compose -f $composeFile down
            }
            "restart" {
                Write-ColorOutput "Restarting services..." $Blue
                & docker-compose -f $composeFile restart
            }
            "logs" {
                Write-ColorOutput "Showing logs..." $Blue
                & docker-compose -f $composeFile logs -f
            }
            "status" {
                Write-ColorOutput "Showing service status..." $Blue
                & docker-compose -f $composeFile ps
            }
            "build" {
                Write-ColorOutput "Building and starting services..." $Blue
                & docker-compose -f $composeFile up -d --build
            }
            "pull" {
                Write-ColorOutput "Pulling latest images..." $Blue
                & docker-compose -f $composeFile pull
            }
            "clean" {
                Write-ColorOutput "Cleaning up..." $Blue
                & docker-compose -f $composeFile down -v --remove-orphans
                & docker system prune -f
            }
            default {
                Write-ColorOutput "X Unknown action: $Action" $Red
                Show-Usage
                exit 1
            }
        }
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker Compose command failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        Write-ColorOutput "X Failed to execute action '$Action': $_" $Red
        exit 1
    }
}

# Function to show service health
function Show-Health {
    Write-ColorOutput "=== Service Health Status ===" $Blue
    
    $composeFile = ""
    if ($Environment -eq "production") {
        $composeFile = "docker-compose.prod.yml"
    } else {
        $composeFile = "docker-compose.yml"
    }
    
    # Get container statuses
    & docker-compose -f $composeFile ps
    
    Write-Host ""
    Write-ColorOutput "=== Container Health Checks ===" $Blue
    
    # Get container IDs
    $containers = & docker-compose -f $composeFile ps -q
    
    if ($containers) {
        foreach ($container in $containers) {
            if ($container) {
                try {
                    $name = & docker inspect --format='{{.Name}}' $container | ForEach-Object { $_.TrimStart('/') }
                    $health = & docker inspect --format='{{.State.Health.Status}}' $container 2>$null
                    
                    if (-not $health) {
                        $health = "no healthcheck"
                    }
                    
                    switch ($health) {
                        "healthy" {
                            Write-ColorOutput "√ ${name}: $health" $Green
                        }
                        "unhealthy" {
                            Write-ColorOutput "X ${name}: $health" $Red
                        }
                        default {
                            Write-ColorOutput "! ${name}: $health" $Yellow
                        }
                    }
                }
                catch {
                    Write-ColorOutput "! Could not check health for container: $container" $Yellow
                }
            }
        }
    }
}

# Function to show usage
function Show-Usage {
    Write-ColorOutput "Usage: .\scripts\deploy.ps1 [-Environment ENVIRONMENT] [-Action ACTION] [-Version VERSION]" $Blue
    Write-Host ""
    Write-ColorOutput "ENVIRONMENT:" $Yellow
    Write-Host "  development (default) - Use docker-compose.yml"
    Write-Host "  production           - Use docker-compose.prod.yml"
    Write-Host ""
    Write-ColorOutput "ACTION:" $Yellow
    Write-Host "  up (default)  - Start services"
    Write-Host "  down          - Stop services"
    Write-Host "  restart       - Restart services"
    Write-Host "  logs          - Show logs"
    Write-Host "  status        - Show service status"
    Write-Host "  build         - Build and start services"
    Write-Host "  pull          - Pull latest images"
    Write-Host "  clean         - Stop services and clean up"
    Write-Host "  health        - Show health status"
    Write-Host ""
    Write-ColorOutput "VERSION:" $Yellow
    Write-Host "  latest (default) - Use latest images"
    Write-Host "  v1.0.0           - Use specific version"
    Write-Host ""
    Write-ColorOutput "Examples:" $Blue
    Write-ColorOutput "  .\scripts\deploy.ps1                                # Start development environment" $Yellow
    Write-ColorOutput "  .\scripts\deploy.ps1 -Environment production -Action up -Version v1.0.0  # Start production with specific version" $Yellow
    Write-ColorOutput "  .\scripts\deploy.ps1 -Environment development -Action logs               # Show development logs" $Yellow
    Write-ColorOutput "  .\scripts\deploy.ps1 -Environment production -Action status             # Show production status" $Yellow
}

# Main execution
function Main {
    # Handle help
    if ($args -contains "--help" -or $args -contains "-h") {
        Show-Usage
        exit 0
    }
    
    # Handle health check
    if ($Action -eq "health") {
        Show-Health
        exit 0
    }
    
    # Run deployment
    Test-Prerequisites
    Initialize-Environment
    Invoke-Deploy
    
    # Show final status
    if ($Action -eq "up" -or $Action -eq "build") {
        Write-Host ""
        Show-Health
    }
    
    Write-Host ""
    Write-ColorOutput "√ Deployment action '$Action' completed successfully!" $Green
}

# Run main function
Main 