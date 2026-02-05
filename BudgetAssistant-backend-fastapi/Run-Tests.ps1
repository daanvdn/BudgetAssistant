# Run-Tests.ps1
# Script to run pytest tests with proper environment configuration
#
# USAGE: .\Run-Tests.ps1
#
# WHAT THIS SCRIPT DOES:
#   1. Activates the Python virtual environment (.venv)
#   2. Sets PYTHONPATH to include 'src' and 'tests' directories
#   3. Runs all pytest tests in .\tests with verbose output
#
# OUTPUT:
#   - Console: Full pytest output (all tests, pass/fail status, errors)
#   - File: pytest-failed.txt - Contains only failure details (FAILURES section + summary)
#     If all tests pass, the file contains "All tests passed!"
#
# FOR COPILOT:
#   - To check test results, read pytest-failed.txt after running this script
#   - If pytest-failed.txt contains failure details, analyze the error messages and tracebacks
#   - The PYTHONPATH is configured so imports from 'src' and 'tests' work correctly

# Get the script's directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Activate the virtual environment
$ActivateScript = Join-Path $ScriptDir ".venv\Scripts\activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
} else {
    Write-Error "Virtual environment not found at $ActivateScript"
    exit 1
}

# Configure PYTHONPATH - add 'src' and 'tests' directories
$SrcPath = Join-Path $ScriptDir "src"
$TestsPath = Join-Path $ScriptDir "tests"

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$SrcPath;$TestsPath;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = "$SrcPath;$TestsPath"
}

Write-Host "PYTHONPATH set to: $env:PYTHONPATH"

# Change to the script directory
Push-Location $ScriptDir

try {
    # Run pytest and capture output while also displaying to console (similar to tee)
    # Using Tee-Object to both display and capture output
    $FailedTestsFile = Join-Path $ScriptDir "pytest-failed.txt"
    # Clear previous failed tests file if exists
    if (Test-Path $FailedTestsFile) {
        Write-Host "Removing previous failed tests file: $FailedTestsFile"
        Remove-Item $FailedTestsFile
    }
    # Run pytest with verbose output, capture all output
    # Use --tb=short for shorter tracebacks in the failures file
    pytest .\tests -v 2>&1 | Tee-Object -Variable pytestOutput

    # Filter and save only the failed tests to the file
    $FailedTests = $pytestOutput | Where-Object {
        $_ -match "FAILED" -or
        $_ -match "^E\s+" -or
        $_ -match "^>\s+" -or
        $_ -match "AssertionError" -or
        $_ -match "Error:" -or
        ($_ -match "^=+ FAILURES =+$") -or
        ($_ -match "^_+ .+ _+$" -and $pytestOutput -match "FAILED")
    }

    # Also capture the full failure details section
    $InFailureSection = $false
    $FailureDetails = @()

    foreach ($line in $pytestOutput) {
        if ($line -match "^=+ FAILURES =+$") {
            $InFailureSection = $true
        }
        if ($InFailureSection) {
            $FailureDetails += $line
        }
        if ($InFailureSection -and $line -match "^=+ short test summary info =+$") {
            # Keep going to capture summary
        }
        if ($line -match "^=+.*=+$" -and $line -notmatch "FAILURES" -and $line -notmatch "short test summary" -and $InFailureSection) {
            if ($line -match "passed|failed|error") {
                $FailureDetails += $line
                break
            }
        }
    }

    # Write failure details to file
    if ($FailureDetails.Count -gt 0) {
        $FailureDetails | Out-File -FilePath $FailedTestsFile -Encoding UTF8
        Write-Host "`nFailed tests saved to: $FailedTestsFile"
    } else {
        # Check if there were any failures in the summary line
        $SummaryLine = $pytestOutput | Where-Object { $_ -match "^\d+ passed" -or $_ -match "failed" }
        if ($SummaryLine -match "failed") {
            "No detailed failure information captured, but tests failed. Re-run with -v for details." | Out-File -FilePath $FailedTestsFile -Encoding UTF8
        } else {
            "All tests passed!" | Out-File -FilePath $FailedTestsFile -Encoding UTF8
            Write-Host "`nAll tests passed!"
        }
    }
}
finally {
    # Return to original directory
    Pop-Location
}
