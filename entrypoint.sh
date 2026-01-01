#!/bin/bash

# Exit on error
set -e

echo "Waiting for database to be ready..."
# Database is already healthy due to depends_on in docker-compose

echo "Running database migrations..."
python manage.py migrate --no-input

echo "Creating superuser if needed..."
# This will only create if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created: admin / admin123")
else:
    print("Superuser already exists")
END

echo "Starting server..."
exec "$@"

