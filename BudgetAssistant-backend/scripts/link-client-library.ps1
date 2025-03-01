param (
    [string]$GeneratedPackagePath = "C:\path\to\generated-package",
    [string]$MainProjectPath = "C:\path\to\main-project",
    [switch]$Unlink
)
#save pwd in variable
$pwd = Get-Location
# Check if npm is installed
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "npm is not installed. Please install Node.js and try again." -ForegroundColor Red
    exit 1
}

if ($Unlink) {
    # Unlink the package
    Write-Host "Unlinking package from main project..." -ForegroundColor Yellow
    Set-Location -Path $MainProjectPath
    npm unlink my-package
    npm install  # Restore dependencies
    Write-Host "Package unlinked successfully." -ForegroundColor Green
    exit 0
}

# Ensure paths exist
if (-Not (Test-Path $GeneratedPackagePath)) {
    Write-Host "Generated package path does not exist: $GeneratedPackagePath" -ForegroundColor Red
    exit 1
}
if (-Not (Test-Path $MainProjectPath)) {
    Write-Host "Main project path does not exist: $MainProjectPath" -ForegroundColor Red
    exit 1
}

# Link the package globally
Write-Host "Linking generated package globally..." -ForegroundColor Cyan
Set-Location -Path $GeneratedPackagePath
npm link

# Link the package in the main project
Write-Host "Linking package in main project..." -ForegroundColor Cyan
Set-Location -Path $MainProjectPath
npm link @daanvdn/budget-assistant-client

Write-Host "Package linked successfully!" -ForegroundColor Green

# Restore original directory
Set-Location -Path $pwd