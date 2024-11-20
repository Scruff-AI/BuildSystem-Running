# Activate the virtual environment
.\ai_code_gen_env\Scripts\Activate.ps1

# Import debug script
. .\BuildSystem_Package\debug_script.ps1

# Log server startup
$logFilePath = "BuildSystem_Package/logs/debug.log"
Write-ServerStartupLog -LogFilePath $logFilePath

# Start the standalone server
python BuildSystem_Package/standalone_server.py

# Example usage for request handling
$requestDetails = "POST /chat/completions HTTP/1.1"
Write-RequestHandlingLog -LogFilePath $logFilePath -RequestDetails $requestDetails

# Example usage for error logging
$errorMessage = "Error processing request"
Write-ErrorLog -LogFilePath $logFilePath -ErrorMessage $errorMessage
