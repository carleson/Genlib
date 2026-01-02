#!/bin/bash

echo "Startar Genlib utvecklingsserver..."
echo ""
echo "För att skapa en superuser, kör:"
echo "  uv run python manage.py createsuperuser"
echo ""
echo "Öppna http://localhost:8000 i din webbläsare"
echo ""

uv run python manage.py runserver
