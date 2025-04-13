#Write-Output "Activating conda environment"
#conda activate budget-assistant-backend-django
Write-Output "Creating pip_packages.txt"
python parse_pip_packages.py

Write-Output "Building Docker image"
docker compose -f ..\docker-compose.yml build
Write-Output "Remove pip_packages.txt if it exists"
Remove-Item ..\pip_packages.txt -ErrorAction SilentlyContinue
