#!/bin/sh
set -e

UI_PORT="${SPECTRE_UI_PORT:-8080}"

echo "Starting SPECTRE demo UI at http://localhost:${UI_PORT}"
nginx

echo ""
echo "============================================================"
echo "Open http://localhost:${UI_PORT} and click Start audit"
echo "WebSocket control server on port ${WS_PORT:-8765}"
echo "============================================================"
echo ""

exec python -m spectre.cli serve --scope-dir /app/scopes
