#!/bin/bash

echo "=========================================="
echo "Startar Genlib med Docker Compose"
echo "=========================================="
echo ""
echo "Detta kommer att:"
echo "  - Bygga Docker-imagen (första gången)"
echo "  - Köra migrationer"
echo "  - Starta servern på http://localhost:8000"
echo ""
echo "OBS: Docker använder en separat SQLite-databas"
echo "     från din lokala utvecklingsmiljö!"
echo ""
echo "Tryck Ctrl+C för att stoppa servern"
echo "=========================================="
echo ""

# Bygg och starta med docker-compose
docker-compose up --build
