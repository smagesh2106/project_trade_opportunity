#!/usr/bin/env bash
set -euo pipefail

cd /home/magesh/02_Projects/project_trade_opportunity/backend

echo "WARNING: This will DESTROY the development PostgreSQL volume."
echo "All current development database data will be lost."
read -r -p "Type RESET-DEV-DB to continue: " confirmation

if [[ "$confirmation" != "RESET-DEV-DB" ]]; then
    echo "Reset cancelled."
    exit 1
fi

echo
echo "Stopping containers and removing development volumes..."
docker compose down -v

echo
echo "Starting fresh PostgreSQL..."
docker compose up -d postgres

echo
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec trade-opportunity-postgres pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; then
        echo "PostgreSQL is ready."
        break
    fi
    sleep 1
done

echo
echo "Applying Alembic migrations..."
alembic upgrade head

echo
echo "Seeding development data..."
python -m app.db.seeds.seed

echo
echo "Fresh development database setup completed."
