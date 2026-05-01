#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@eventhub.com').exists() or User.objects.create_superuser(email='admin@eventhub.com', username='SystemAdmin', password='Admin1234!', role='system_admin')" | python manage.py shell