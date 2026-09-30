#!/bin/bash
set -e

echo "Running database migrations..."

# Run injury fields migration
python migrate_add_injury_fields.py || echo "Migration migrate_add_injury_fields.py already applied or failed"

echo "Starting bot..."
exec python main.py
