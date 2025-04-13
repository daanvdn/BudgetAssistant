cd ..\api
npm init -y
npm install


# Fetch existing versions, ensuring an empty array does not break jq
$versions = npm view @daanvdn/budget-assistant-client versions --json --registry=https://npm.pkg.github.com
if (-not $versions) {
    $versions = "[]"
}
Write-Output "Existing versions: $versions"

# Find the most recent version
$latestVersion = $versions | ConvertFrom-Json | Sort-Object | Select-Object -Last 1
Write-Output "Latest version: $latestVersion"

# Increment the minor version number by 1
$versionParts = $latestVersion -split '\.'
$major = $versionParts[0]
$minor = [int]$versionParts[1] + 1
$newVersion = "$major.$minor.0"
Write-Output "New version: $newVersion"

# Update package.json
$packageJson = Get-Content -Raw -Path package.json | ConvertFrom-Json
$packageJson.name = "@daanvdn/budget-assistant-client"
$packageJson.version = $newVersion
$packageJson.main = "index.js"
$packageJson.types = "index.d.ts"
$packageJson.files = @("**/*")
$packageJson.publishConfig = @{
    "@daanvdn:registry" = "https://npm.pkg.github.com"
}

# Replace placeholders
$packageJsonString = $packageJson | ConvertTo-Json -Depth 10
$packageJsonString = $packageJsonString -replace "GIT_USER_ID", "daanvdn"
$packageJsonString = $packageJsonString -replace "GIT_REPO_ID", "BudgetAssistant"

# Save updated package.json
$packageJsonString | Out-File -FilePath package.json -Encoding utf8

# Store full package name in environment variable
$env:PACKAGE_NAME = "budget-assistant-client-$newVersion.tgz"
Add-Content -Path $env:GITHUB_ENV -Value "PACKAGE_NAME=budget-assistant-client-$newVersion.tgz"