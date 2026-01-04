#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --no-input

echo "Creating superuser (if needed)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin / admin123')
"

echo "Starting server..."
exec "$@"
