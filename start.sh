#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Starting Smart-EMAP (backend + Vite dev + dist + optional file watcher)..."
exec python3 start.py
