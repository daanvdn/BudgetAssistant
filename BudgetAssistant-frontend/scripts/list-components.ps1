# List all Angular components in the project
# Components are identified by files ending with .component.ts

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Split-Path -Parent $scriptDir
$srcDir = Join-Path $frontendDir "src"

Write-Host "Scanning for Angular components in: $srcDir" -ForegroundColor Cyan
Write-Host ""

# Find all .component.ts files
$components = Get-ChildItem -Path $srcDir -Recurse -Filter "*.component.ts" |
    Where-Object { $_.FullName -notmatch "node_modules" } |
    Sort-Object Name

Write-Host "Found $($components.Count) components:" -ForegroundColor Green
Write-Host ""

# Output as a table
$components | ForEach-Object {
    $relativePath = $_.FullName.Replace($srcDir, "").TrimStart("\")
    [PSCustomObject]@{
        ComponentFile = $_.Name
        Directory = $_.DirectoryName
    }
} | Format-Table -AutoSize

# Also output as TSV format for use with generate_plans.py
$tsvOutputPath = Join-Path $frontendDir "componentlist.tsv"
$tsvContent = $components | ForEach-Object {
    "$($_.Name)`t$($_.DirectoryName)"
}
$tsvContent | Out-File -FilePath $tsvOutputPath -Encoding UTF8

Write-Host ""
Write-Host "TSV file saved to: $tsvOutputPath" -ForegroundColor Yellow

