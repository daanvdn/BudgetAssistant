#!/bin/bash -x
set -e
set -x

# Check if TRUNCATE_TABLES environment variable is set
if [ "${TRUNCATE_TABLES}" = "true" ]; then
    echo "TRUNCATE_TABLES flag is set to true. Will truncate database tables after migrations."
    SHOULD_TRUNCATE=true
else
  echo "TRUNCATE_TABLES flag is not set or set to false. Will not truncate database tables."
    SHOULD_TRUNCATE=false
fi

# Wait for the database to be ready
/wait-for-it.sh db:3306 --timeout=60 --strict -- echo "Database is up"
echo "Running makemigrations..."
python manage.py makemigrations
echo "Running migrations..."
python manage.py migrate

# Truncate tables if flag is set
if [ "$SHOULD_TRUNCATE" = true ]; then
    echo "Truncating database tables..."
    python manage.py truncate_tables
    echo "Database tables truncated."
fi

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Creating superuser if it does not yet exist..."
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    username = os.environ['DJANGO_SUPERUSER_USERNAME']
    email = os.environ['DJANGO_SUPERUSER_EMAIL']
    password = os.environ['DJANGO_SUPERUSER_PASSWORD']

    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser {username} created.")
else:
    print("Superuser already exists.")
EOF

# Start the Django application
exec "$@"
