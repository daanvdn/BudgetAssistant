#check if conda env budget-assistant-backend-django is activated. if not then activate it
$envName = "budget-assistant-backend-django"
# Get the currently active Conda environment
$activeEnv = $env:CONDA_DEFAULT_ENV
if ($activeEnv -ne $envName)
{
    Write-Output "Activating Conda environment: $envName"
    conda activate $envName
}
else
{
    Write-Output "Conda environment '$envName' is already active."
}
Write-Output "Creating pip_packages.txt"
python parse_pip_packages.py

Write-Output "Building Docker image"
docker compose -f ..\docker-compose.yml build
Write-Output "Remove pip_packages.txt if it exists"
Remove-Item ..\pip_packages.txt -ErrorAction SilentlyContinue
