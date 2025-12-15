# GenAI CloudOps - Docker Build Script (PowerShell)
# This script builds Docker images for both frontend and backend services

param(
    [string]$Version = "latest",
    [string]$Environment = "development", 
    [string]$Registry = "",
    [string]$Push = "false"
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

Write-ColorOutput "=== GenAI CloudOps Docker Build Script ===" $Blue
Write-ColorOutput "Version: $Version" $Yellow
Write-ColorOutput "Environment: $Environment" $Yellow
Write-ColorOutput "Registry: $(if($Registry) {$Registry} else {'local'})" $Yellow
Write-ColorOutput "Push to registry: $Push" $Yellow
Write-Host ""

# Function to build and tag images
function Build-Image {
    param(
        [string]$Service,
        [string]$Dockerfile,
        [string]$Context,
        [string]$Target = ""
    )
    
    Write-ColorOutput "Building $Service image..." $Blue
    
    # Build command components
    $buildArgs = @(
        "build",
        "-f", "$Context/$Dockerfile",
        "-t", "genai-cloudops-${Service}:$Version",
        "-t", "genai-cloudops-${Service}:latest"
    )
    
    if ($Target) {
        $buildArgs += "--target", $Target
    }
    
    if ($Registry) {
        $buildArgs += "-t", "$Registry/genai-cloudops-${Service}:$Version"
        $buildArgs += "-t", "$Registry/genai-cloudops-${Service}:latest"
    }
    
    $buildArgs += $Context
    
    Write-ColorOutput "Executing: docker $($buildArgs -join ' ')" $Yellow
    
    try {
        & docker @buildArgs
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ $Service image built successfully" $Green
        } else {
            throw "Docker build failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        Write-ColorOutput "✗ Failed to build $Service image: $_" $Red
        exit 1
    }
}

# Function to push images
function Push-Image {
    param([string]$Service)
    
    if ($Registry -and $Push -eq "true") {
        Write-ColorOutput "Pushing $Service image to registry..." $Blue
        
        try {
            & docker push "$Registry/genai-cloudops-${Service}:$Version"
            & docker push "$Registry/genai-cloudops-${Service}:latest"
            
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ $Service image pushed successfully" $Green
            } else {
                throw "Docker push failed with exit code $LASTEXITCODE"
            }
        }
        catch {
            Write-ColorOutput "✗ Failed to push $Service image: $_" $Red
            exit 1
        }
    }
}

# Check if Docker is running
try {
    & docker info | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed"
    }
}
catch {
    Write-ColorOutput "✗ Docker is not running. Please start Docker and try again." $Red
    exit 1
}

# Determine Dockerfile and target based on environment
if ($Environment -eq "production") {
    $BackendDockerfile = "Dockerfile"
    $FrontendDockerfile = "Dockerfile" 
    $Target = "production"
} else {
    $BackendDockerfile = "Dockerfile.dev"
    $FrontendDockerfile = "Dockerfile.dev"
    $Target = ""
}

# Build backend image
Build-Image -Service "backend" -Dockerfile $BackendDockerfile -Context "./backend" -Target $Target

# Build frontend image
Build-Image -Service "frontend" -Dockerfile $FrontendDockerfile -Context "./frontend" -Target $Target

# Push images if requested
Push-Image -Service "backend"
Push-Image -Service "frontend"

# Show built images
Write-Host ""
Write-ColorOutput "=== Built Images ===" $Green
& docker images | Where-Object { $_ -match "genai-cloudops" }

Write-Host ""
Write-ColorOutput "✓ Build completed successfully!" $Green

# Usage instructions
Write-Host ""
Write-ColorOutput "Usage examples:" $Blue
Write-ColorOutput "  .\scripts\build.ps1                                    # Build latest development images" $Yellow
Write-ColorOutput "  .\scripts\build.ps1 -Version v1.0.0 -Environment production  # Build production v1.0.0" $Yellow
Write-ColorOutput "  .\scripts\build.ps1 -Version v1.0.0 -Environment production -Registry myregistry.com -Push true  # Build, tag and push to registry" $Yellow 