Write-Output "Activating conda environment"
conda activate budget-assistant-backend-django
Write-Output "Running migrations"
python manage.py migrate
Write-Output "Starting Django server"
python manage.py runserver
