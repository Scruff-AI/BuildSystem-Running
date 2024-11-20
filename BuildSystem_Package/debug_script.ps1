# Debug Script for BuildSystem_Package

# Function to check if a path is a URL
function Test-IsUrl {
    param (
        [string]$Path
    )
    return $Path -match '^https?://'
}

# Function to log server startup
function Write-ServerStartupLog {
    param (
        [string]$LogFilePath
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] Server started."
    Add-Content -Path $LogFilePath -Value $logMessage
}

# Function to log request handling
function Write-RequestHandlingLog {
    param (
        [string]$LogFilePath,
        [string]$RequestDetails
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] Handling request: $RequestDetails"
    Add-Content -Path $LogFilePath -Value $logMessage
}

# Function to log errors with full context
function Write-ErrorLog {
    param (
        [string]$LogFilePath,
        [string]$ErrorMessage,
        [System.Management.Automation.ErrorRecord]$ErrorRecord
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $errorDetails = @"
[$timestamp] Error Details:
Message: $ErrorMessage
Exception Type: $($ErrorRecord.Exception.GetType().FullName)
Exception Message: $($ErrorRecord.Exception.Message)
Script Stack Trace: $($ErrorRecord.ScriptStackTrace)
Position: $($ErrorRecord.InvocationInfo.PositionMessage)
Line: $($ErrorRecord.InvocationInfo.Line)
Category: $($ErrorRecord.CategoryInfo.Category)
Target Object: $($ErrorRecord.TargetObject)
Fully Qualified Error ID: $($ErrorRecord.FullyQualifiedErrorId)
"@
    Add-Content -Path $LogFilePath -Value $errorDetails
    
    # Also log to error_debug.log for more visibility
    $errorLogPath = Join-Path (Split-Path $LogFilePath -Parent) "error_debug.log"
    Add-Content -Path $errorLogPath -Value $errorDetails
}

# Function to update log file with rotation
function Update-LogFile {
    param (
        [string]$LogFilePath,
        [int]$MaxLogSizeMB = 50  # Increased from 10MB to 50MB
    )
    if (Test-Path $LogFilePath) {
        $logFile = Get-Item -Path $LogFilePath
        if ($logFile.Length -gt ($MaxLogSizeMB * 1MB)) {
            $backupLogFilePath = "$($logFile.DirectoryName)\$($logFile.BaseName)_$(Get-Date -Format "yyyyMMddHHmmss").log"
            Move-Item -Path $LogFilePath -Destination $backupLogFilePath
            New-Item -Path $LogFilePath -ItemType File | Out-Null
            Write-ServerStartupLog -LogFilePath $LogFilePath
        }
    }
}

# Main script to integrate debug functions
$logFilePath = "BuildSystem_Package/logs/debug.log"

# Create logs directory if it doesn't exist
$logsDir = Split-Path $logFilePath -Parent
if (-not (Test-Path $logsDir)) {
    New-Item -Path $logsDir -ItemType Directory | Out-Null
}

# Create log file if it doesn't exist
if (-not (Test-Path $logFilePath)) {
    New-Item -Path $logFilePath -ItemType File | Out-Null
}

# Create error_debug.log if it doesn't exist
$errorLogPath = Join-Path $logsDir "error_debug.log"
if (-not (Test-Path $errorLogPath)) {
    New-Item -Path $errorLogPath -ItemType File | Out-Null
}

# Update log files if they exceed the maximum size
Update-LogFile -LogFilePath $logFilePath -MaxLogSizeMB 50
Update-LogFile -LogFilePath $errorLogPath -MaxLogSizeMB 50

# Log server startup
Write-ServerStartupLog -LogFilePath $logFilePath

# Example usage for request handling
$requestDetails = "POST /chat/completions HTTP/1.1"
Write-RequestHandlingLog -LogFilePath $logFilePath -RequestDetails $requestDetails

# Example usage for error logging with full context
try {
    throw "Error processing request"
} catch {
    Write-ErrorLog -LogFilePath $logFilePath -ErrorMessage $_.Exception.Message -ErrorRecord $_
}
