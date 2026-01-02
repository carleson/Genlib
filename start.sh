#!/usr/bin/env bash
set -e

# Starta genlib-servern
(
  cd /home/johan/repos/projekt/genlib/
  source .venv/bin/activate
  exec ./run_server.sh
) &

# Starta arkivdigital webapp
(
  cd /home/johan/repos/projekt/arkivdigital-tool
  source .venv/bin/activate
  exec uv run python web_app.py
) &

# Vänta så att scriptet inte avslutas direkt
wait

