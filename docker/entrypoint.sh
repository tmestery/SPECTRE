#!/bin/sh
set -e

UI_PORT="${SPECTRE_UI_PORT:-8080}"
UI_DELAY="${SPECTRE_UI_DELAY:-3}"

echo "Starting SPECTRE demo UI at http://localhost:${UI_PORT}"
nginx

echo "Waiting ${UI_DELAY}s for the dashboard..."
sleep "$UI_DELAY"

echo ""
echo "============================================================"
echo "Open http://localhost:${UI_PORT}"
echo "Repo:   ${SPECTRE_REPO}"
echo "Branch: ${SPECTRE_BRANCH:-main}"
echo ""
echo "When the session_id JSON line appears below, connect in the UI"
echo "or open http://localhost:${UI_PORT}/?session=<session_id>"
echo "============================================================"
echo ""

exec python -m spectre.cli run \
  --repo "${SPECTRE_REPO}" \
  --scope "${SPECTRE_SCOPE:-scopes/spectre.yaml}" \
  --branch "${SPECTRE_BRANCH:-main}" \
  --ws
