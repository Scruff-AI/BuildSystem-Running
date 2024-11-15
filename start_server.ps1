# Start the server
Write-Host "Starting BuildSystem Server..."
Write-Host "=" * 60
Write-Host "Server Configuration:"
Write-Host "- Base URL: http://localhost:3000"
Write-Host "- API Key: sk-DQppd0KyYa4yWIgsFsVRxotAK3b9AWxbsb3OOsf1WjT3BlbkFJRpXkZZW851KA65"
Write-Host "- Model ID: agent-system"
Write-Host "=" * 60

# Activate virtual environment if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
}

try {
    python src/standalone_server.py
}
finally {
    Write-Host "`nServer stopped"
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        deactivate
    }
    
    # Kill any remaining python processes
    Get-Process | Where-Object {$_.ProcessName -eq 'python' -and $_.CommandLine -like '*standalone_server.py*'} | Stop-Process -Force
}
