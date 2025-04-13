#get the absolute path of the pwd and assign to variable
#check if conda env budget-assistant-backend-django is activated. if not then activate it
$envName = "budget-assistant-backend-django"

# Get the currently active Conda environment
$activeEnv = $env:CONDA_DEFAULT_ENV

if ($activeEnv -ne $envName) {
    Write-Output "Activating Conda environment: $envName"
    conda activate $envName
} else {
    Write-Output "Conda environment '$envName' is already active."
}


$pwd_absolute_path = (Get-Location).Path
if (Test-Path ..\generated-api) { Remove-Item ..\generated-api -Recurse -Force }


echo "Initializing local npm registry (Verdaccio)"
..\..\BudgetAssistant-frontend\scripts\start-verdaccio.ps1

#$AuthToken = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("<username>:<password>"))
#echo "$AuthToken"

$local_registry = "http://localhost:4873"
#get absolute path to .npmrc
$npmrc_path = (Resolve-Path .npmrc).Path
$env:NPM_CONFIG_USERCONFIG = $npmrc_path
echo "absolute path to .npmrc: $npmrc_path"

#echo "Logging in to local npm registry"
#npm login --registry=$local_registry --scope=@daanvdn --always-auth=true

#loging to the local npm registry. get the username and password from the .env file
npm whoami  --registry=$local_registry --scope=@daanvdn
#fail if whoami was not successful
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm login failed. Please check your credentials." -ForegroundColor Red
    exit 1
}

Write-Output "Unpublishing the package from local npm registry if needed"
#get the absolute path to .\api

# Fetch existing versions, ensuring an empty array does not break jq
$versions = npm view @daanvdn/budget-assistant-client versions --json --registry=$local_registry 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Output "The package already exists. Unpublishing the package from local npm registry"
    npm unpublish @daanvdn/budget-assistant-client -f --registry=$local_registry
} else {
    Write-Output "Package does not exist in registry"
    $versions = @()
}

#print activating conda environment
echo "Activating conda environment"
conda activate budget-assistant-backend-django
#set the TEST_MODE environment variable to true
$env:TEST_MODE = "true"
echo "generating openapi schema"
python ..\manage.py spectacular --color --file schema.yml

echo "Generating Angular API"
if (Test-Path ..\generated-api)
{
    Remove-Item ..\generated-api -Recurse -Force
}
openapi-generator-cli generate -i schema.yml -g typescript-angular -o ../generated-api --additional-properties=modelPropertyNaming=camelCase,fileNaming=kebab-case,enumPropertyNaming=original,ngVersion=18.2.13,npmName=budget-assistant-client,serviceSuffix=BudgetAssistantBackendClientService,serviceFileSuffix=-budget-assistant-backend-client.service

# Add timestamp to package.json
$timestamp = [DateTime]::Now.ToString("o")
Write-Output "Adding timestamp: $timestamp"

Write-Output "Installing npm dependencies"

cd ..\generated-api
npm init -y
npm install

Write-Output "Building Angular library"
npm run build

Write-Output "Packaging npm module"

# Update package.json
# Convert to PSCustomObject with new properties
$packageJson = [PSCustomObject]@{
    name = "@daanvdn/budget-assistant-client"
    version = "1.0.0"
    main = "dist/bundles/budget-assistant-client.umd.js"
    module = "dist/fesm2022/budget-assistant-client.mjs"
    es2022 = "dist/fesm2022/budget-assistant-client.mjs"
    esm2022 = "dist/esm2022/budget-assistant-client.mjs"
    fesm2022 = "dist/fesm2022/budget-assistant-client.mjs"
    typings = "dist/index.d.ts"
    type = "module"
    sideEffects = $false
    exports = @{
        "." = @{
            types = "./dist/index.d.ts"
            esm2022 = "./dist/esm2022/budget-assistant-client.mjs"
            es2022 = "./dist/fesm2022/budget-assistant-client.mjs"
            es2020 = "./dist/fesm2022/budget-assistant-client.mjs"
            es2015 = "./dist/fesm2022/budget-assistant-client.mjs"
            node = "./dist/fesm2022/budget-assistant-client.mjs"
            default = "./dist/fesm2022/budget-assistant-client.mjs"
        }
        "./package.json" = "./package.json"
    }
    files = @("dist/**/*")
    publishConfig = @{
        "@daanvdn:registry" = $local_registry
    }
    generatedAt = $timestamp
}

# Preserve existing properties from the original package.json
$originalJson = Get-Content -Raw -Path package.json -Encoding utf8 | ConvertFrom-Json
Write-Output "Original package.json properties: $($originalJson.PSObject.Properties.Name -join ', ')"
foreach ($property in $originalJson.PSObject.Properties) {
    if (-not $packageJson.PSObject.Properties[$property.Name]) {
        $packageJson | Add-Member -NotePropertyName $property.Name -NotePropertyValue $property.Value
    }
}

# Replace placeholders
$packageJsonString = $packageJson | ConvertTo-Json -Compress -Depth 100
$packageJsonString = $packageJsonString -replace "\\u003e", ">" -replace "\\u003c", "<"
$packageJsonString = $packageJsonString -replace "GIT_USER_ID", "daanvdn"
$packageJsonString = $packageJsonString -replace "GIT_REPO_ID", "BudgetAssistant"

Write-Output "Updated package.json: $packageJsonString"

# Save updated package.json
#$packageJsonString | Out-File -FilePath package.json -Encoding utf8
# Replace the current WriteAllText line with this:
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("$pwd\package.json", $packageJsonString, $utf8NoBom)
# Store full package name in environment variable
$env:PACKAGE_NAME = "budget-assistant-client-1.0.0.tgz"
npm pack

Write-Output "Publishing npm module to local registry"
npm publish --access public --registry=$local_registry

# Make sure the compiled library is included in the package
Write-Output "Verifying package contents"
if (Test-Path $env:PACKAGE_NAME) {
    Write-Output "Package created successfully: $env:PACKAGE_NAME"
    # Extract the package to verify its contents
    if (Test-Path package-contents) { Remove-Item package-contents -Recurse -Force }
    mkdir package-contents
    tar -xf $env:PACKAGE_NAME -C package-contents
    Write-Output "Package contents:"
    Get-ChildItem -Path package-contents\package -Recurse | Select-Object FullName
    # Clean up
    Remove-Item package-contents -Recurse -Force
} else {
    Write-Output "Warning: Package was not created successfully"
}

Write-Output "Re-install latest version in frontend"
cd ..\..\BudgetAssistant-frontend

Write-Output "Removing node_modules/@daanvdn/budget-assistant-client from BudgetAssistant-frontend"
if (Test-Path node_modules/@daanvdn/budget-assistant-client) { Remove-Item node_modules/@daanvdn/budget-assistant-client -Recurse -Force }
#make sure that the latest version is re-installed. The version number always is 1.0.0 but the contents of the package can change. So we need to force re-install
npm install @daanvdn/budget-assistant-client --save --registry "http://localhost:4873" --userconfig "C:\Users\daanv\Git\BudgetAssistant\BudgetAssistant-backend\scripts\.npmrc" --force

cd $pwd_absolute_path
Write-Output "Removing temporary files"
if (Test-Path schema.yml) { Remove-Item schema.yml -Force }
if (Test-Path ..\node_modules\@daanvdn) { Remove-Item ..\node_modules\@daanvdn -Recurse -Force }
# Keep the generated-api directory for reference
# if (Test-Path ..\generated-api) { Remove-Item ..\generated-api -Recurse -Force }
if (Test-Path package.json) { Remove-Item package.json -Force }
if (Test-Path package-lock.json) { Remove-Item package-lock.json -Force }
if (Test-Path ..\package.json) { Remove-Item ..\package.json -Force }
if (Test-Path ..\package-lock.json) { Remove-Item ..\package-lock.json -Force }

# Create a README file explaining the generated library
$readmeContent = @"
# Budget Assistant Client Library

This directory contains the generated Angular client library for the Budget Assistant API.

## Contents

- Source code: TypeScript source files generated from the OpenAPI schema
- Compiled library: JavaScript files compiled from the TypeScript sources (in the 'dist' directory)

## Usage

The library is published to the local npm registry and installed in the frontend project.
To use it in the frontend, import the services and models from '@daanvdn/budget-assistant-client'.

Example:
```typescript
import { ApiService, ModelClass } from '@daanvdn/budget-assistant-client';
```

## Module Resolution

This library is configured as an ES module with proper package exports. Angular should be able to resolve
it directly from node_modules without needing special path mappings in tsconfig.json.

If you previously had this in your tsconfig.json:
```json
"paths": {
  "@daanvdn/budget-assistant-client": [
    "node_modules/@daanvdn/budget-assistant-client"
  ]
}
```

You should now be able to remove it, as the library is properly configured for Angular's module resolution.
"@

# Ensure the generated-api directory exists
if (-not (Test-Path ..\generated-api)) {
    New-Item -Path ..\generated-api -ItemType Directory -Force
}

if (-not (Test-Path ..\generated-api\README.md)) {
    $readmeContent | Out-File -FilePath ..\generated-api\README.md -Encoding utf8
}

Write-Output "Angular API generation and installation complete"
