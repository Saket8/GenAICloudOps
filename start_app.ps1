# start_app.ps1

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"
$venvPath = Join-Path $backendPath "venv\Scripts\Activate.ps1"

function Start-Backend {
    Write-Host "Starting Backend..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$venvPath'; cd '$backendPath'; python -m uvicorn main:app --reload --env-file .env"
}

function Start-Frontend {
    Write-Host "Starting Frontend..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"
}

function Stop-Processes {
    # This is a bit tricky to target specific windows without IDs, 
    # but for a dev script, we might just rely on the user closing them 
    # or just spawning new ones. 
    # A more robust way would be to track PIDs, but Start-Process -PassThru 
    # returns the process object for the shell, not the child python/node process usually.
    
    # For simplicity in this version, we'll just spawn new ones and let the user close old ones
    # or we can try to kill by port if we want to be aggressive, but that's risky.
    
    # Let's just inform the user.
    Write-Host "Note: This script spawns new windows. Please close old ones manually if they don't close." -ForegroundColor Yellow
}

# Initial Start
Start-Backend
Start-Frontend

while ($true) {
    Write-Host "`nOptions:" -ForegroundColor Cyan
    Write-Host "1. Restart Backend"
    Write-Host "2. Restart Frontend"
    Write-Host "3. Restart Both"
    Write-Host "4. Exit"
    
    $choice = Read-Host "Enter choice (1-4)"
    
    switch ($choice) {
        "1" { 
            Start-Backend 
        }
        "2" { 
            Start-Frontend 
        }
        "3" { 
            Start-Backend
            Start-Frontend
        }
        "4" { 
            exit 
        }
        default { 
            Write-Host "Invalid choice" -ForegroundColor Red 
        }
    }
}
