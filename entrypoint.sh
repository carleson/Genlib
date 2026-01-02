#!/bin/bash

set -e

echo "Startar Genlib..."

echo "Kör migrationer..."
python manage.py migrate --noinput

echo "Samlar statiska filer..."
python manage.py collectstatic --noinput --clear

echo "Skapar superuser om den inte finns..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print("Skapar admin-användare...")
    print("Användarnamn: admin")
    print("Lösenord: admin")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
else:
    print("Admin-användare finns redan")
EOF

echo ""
echo "=========================================="
echo "Genlib är redo!"
echo "Öppna http://localhost:8000 i din webbläsare"
echo ""
echo "Admin-inloggning:"
echo "  Användarnamn: admin"
echo "  Lösenord: admin"
echo "=========================================="
echo ""

exec "$@"
