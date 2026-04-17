#!/bin/sh
set -e

python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
email = "$DJANGO_SUPERUSER_EMAIL"
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password="$DJANGO_SUPERUSER_PASSWORD",
        first_name="${DJANGO_SUPERUSER_FIRST_NAME:-Admin}",
        last_name="${DJANGO_SUPERUSER_LAST_NAME:-User}",
    )
    print(f"Superuser {email} created.")
else:
    print(f"Superuser {email} already exists.")
EOF
fi

exec python manage.py runserver 0.0.0.0:8000