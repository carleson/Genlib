#!/bin/bash

echo "========================================="
echo "  Genlib - Släktforskningshantering"
echo "========================================="
echo ""

# Kontrollera om detta är första körningen
if [ ! -f "db.sqlite3" ]; then
    echo "🔍 Första körningen detekterad!"
    echo "   Kör automatisk databas-initiering..."
    echo ""
fi

# Kör migrations automatiskt
echo "📦 Uppdaterar databas..."
uv run python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo "✅ Databas uppdaterad!"
else
    echo "❌ Fel vid uppdatering av databas!"
    exit 1
fi

echo ""

# Kontrollera om setup är klar
SETUP_COMPLETE=$(uv run python -c "
import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import SetupStatus
try:
    status = SetupStatus.load()
    print('true' if status.is_completed else 'false')
except:
    print('false')
" 2>/dev/null)

if [ "$SETUP_COMPLETE" = "false" ]; then
    echo "🚀 Initial setup krävs!"
    echo ""
    echo "   Öppna din webbläsare på:"
    echo "   👉 http://localhost:8000/setup/"
    echo ""
    echo "   Du kommer automatiskt att omdirigeras till setup-sidan."
    echo "   Där kan du:"
    echo "   • Skapa ditt administratörskonto"
    echo "   • Konfigurera var media-filer ska lagras"
    echo ""
else
    echo "✅ Setup är klar!"
    echo ""
    echo "   Öppna din webbläsare på:"
    echo "   👉 http://localhost:8000"
    echo ""
fi

echo "========================================="
echo "  Startar utvecklingsserver..."
echo "========================================="
echo ""

uv run python manage.py runserver
