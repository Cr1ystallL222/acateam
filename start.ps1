# Start all services for Afisha Cinema
# Run this script from project root

$host.UI.RawUI.WindowTitle = "Afisha Cinema Launcher"

Write-Host "Starting Afisha Cinema Services..." -ForegroundColor Cyan
Write-Host ""

# Start Backend API
Write-Host "[1/4] Starting Backend API on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; uvicorn api.main:app --reload --port 8000"

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "[2/4] Starting Frontend on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\web'; npm run dev"

Start-Sleep -Seconds 2

# Start Main Bot
Write-Host "[3/4] Starting Main Telegram Bot..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; py bots/bot.py"

Start-Sleep -Seconds 1

# Start Auth Bot
Write-Host "[4/4] Starting Auth Telegram Bot..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; py bots/auth_bot.py"

Write-Host ""
Write-Host "All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API:      http://127.0.0.1:8000" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to close this launcher (services will keep running)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
