#!/bin/bash

echo "=========================================="
echo "GENLIB BACKUP"
echo "=========================================="
echo ""
echo "Skapar komplett backup av:"
echo "  ✓ Databas (SQLite)"
echo "  ✓ Alla uppladdade filer (media/)"
echo "  ✓ Konfigurationsfiler"
echo ""
echo "=========================================="
echo ""

# Kör backup-kommandot
uv run python manage.py backup

echo ""
echo "=========================================="
echo "Backup klar!"
echo ""
echo "Backup-filer finns i katalogen: backups/"
echo ""
echo "För att återställa en backup, kör:"
echo "  ./restore.sh backups/genlib_backup_YYYY-MM-DD_HH-MM-SS.zip"
echo "=========================================="
