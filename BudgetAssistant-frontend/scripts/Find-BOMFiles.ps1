# Script to find files with Byte Order Mark (BOM)
param(
    [string]$directory = ".",   # Default to current directory
    [string]$filter = "*.*"     # Default to all files
)

# Function to check if a file has a BOM
function Has-BOM {
    param ([string]$filePath)

    try {
        # Read first 3 bytes of the file
        $fileStream = [System.IO.File]::OpenRead($filePath)
        $bytes = New-Object byte[] 3
        $bytesRead = $fileStream.Read($bytes, 0, 3)
        $fileStream.Close()

        # Check if the bytes match UTF-8 BOM (0xEF,0xBB,0xBF)
        if ($bytesRead -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            return $true
        }

        return $false
    }
    catch {
        Write-Host "Error reading file $filePath : $_" -ForegroundColor Red
        return $false
    }
}

# Get all files recursively
Write-Host "Scanning directory: $directory for files with BOM mark..." -ForegroundColor Cyan
$allFiles = @(Get-ChildItem -Path $directory -Recurse -File -Filter $filter)
$totalFiles = $allFiles.Count
$filesWithBom = @()
$processed = 0
$spinChars = '|', '/', '-', '\'
$startTime = Get-Date

Write-Host "Found $totalFiles files to check"

foreach ($file in $allFiles) {
    $filePath = $file.FullName

    # Update progress indicator
    $processed++
    $percentComplete = [math]::Round(($processed / $totalFiles) * 100, 1)
    $elapsed = (Get-Date) - $startTime
    $estimatedTotal = $elapsed.TotalSeconds / ($processed / $totalFiles)
    $remaining = $estimatedTotal - $elapsed.TotalSeconds

    # Create progress message with spinner
    $spinChar = $spinChars[$processed % $spinChars.Length]
    $progressMessage = "$spinChar Progress: $processed/$totalFiles ($percentComplete%) - Remaining: $([math]::Round($remaining, 0))s"

    # Clear current line and write progress without newline
    Write-Host "`r$progressMessage" -NoNewline

    # Check for BOM
    if (Has-BOM -filePath $filePath) {
        $filesWithBom += $filePath
        # Clear progress line before writing BOM message
        Write-Host "`r                                                                          " -NoNewline
        Write-Host "`rBOM found in: $filePath" -ForegroundColor Yellow
        # Rewrite progress after BOM message
        Write-Host "`r$progressMessage" -NoNewline
    }
}

# Clear progress line
Write-Host "`r                                                                          " -NoNewline

# Summary
$elapsed = (Get-Date) - $startTime
Write-Host "`nScan completed in $([math]::Round($elapsed.TotalSeconds, 1)) seconds" -ForegroundColor Cyan

if ($filesWithBom.Count -eq 0) {
    Write-Host "No files with BOM mark found." -ForegroundColor Green
} else {
    Write-Host "Found $($filesWithBom.Count) files with BOM mark:" -ForegroundColor Yellow
    $filesWithBom | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
}