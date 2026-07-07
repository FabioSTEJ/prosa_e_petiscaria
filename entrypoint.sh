#!/bin/sh
set -e

if [ ! -f /app/data/.seeded ]; then
    python scripts/seed_admin.py
    touch /app/data/.seeded
fi

exec python run.py
