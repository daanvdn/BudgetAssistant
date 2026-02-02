#!/bin/bash
#
# Docker entrypoint script for Budget Tracker Backend
# Runs database migrations before starting the application
#

set -e

echo "=== Budget Tracker Backend Startup ==="

# Run auto-migration script (handles new and existing databases)
cd /app
uv run python auto_migrate.py

# Start the application
echo "Starting application..."
exec "$@"

