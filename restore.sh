#!/bin/bash

if [ -z "$1" ]; then
    echo "=========================================="
    echo "GENLIB RESTORE"
    echo "=========================================="
    echo ""
    echo "Användning: ./restore.sh <backup-fil> [flaggor]"
    echo ""
    echo "Exempel:"
    echo "  ./restore.sh backups/genlib_backup_2025-12-11_14-30-00.zip"
    echo "  ./restore.sh backups/genlib_backup_2025-12-11_14-30-00.zip --db-only"
    echo "  ./restore.sh backups/genlib_backup_2025-12-11_14-30-00.zip --exclude-media"
    echo ""
    echo "Flaggor:"
    echo "  --db-only        Återställ endast databas"
    echo "  --exclude-media  Återställ databas och konfiguration (utan media)"
    echo "  --no-confirm     Hoppa över bekräftelse"
    echo ""
    echo "Tillgängliga backups:"
    echo ""

    if [ -d "backups" ]; then
        ls -lht backups/*.zip 2>/dev/null | head -10 || echo "  Inga backups hittades"
    else
        echo "  Inga backups hittades (katalogen 'backups/' finns inte)"
    fi

    echo ""
    echo "=========================================="
    exit 1
fi

BACKUP_FILE="$1"
shift  # Ta bort första argumentet, resten är flaggor

echo "=========================================="
echo "GENLIB RESTORE"
echo "=========================================="
echo ""
echo "Återställer från: $BACKUP_FILE"
echo ""
echo "⚠️  VARNING: Detta kommer att:"
echo "  - Skriva över nuvarande databas"
echo "  - Skriva över media-filer (om inte --db-only eller --exclude-media används)"
echo "  - Skapa säkerhetskopia av nuvarande data"
echo ""
echo "=========================================="
echo ""

# Kör restore-kommandot med alla extra flaggor
uv run python manage.py restore "$BACKUP_FILE" "$@"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Återställning klar!"
    echo ""
    echo "⚠️  VIKTIGT: Starta om servern för att ladda nya data!"
    echo ""
    echo "Om du kör servern, stoppa den (Ctrl+C) och kör:"
    echo "  ./run_server.sh"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Återställning misslyckades!"
    echo "Se felmeddelanden ovan för mer information."
    echo "=========================================="
fi
