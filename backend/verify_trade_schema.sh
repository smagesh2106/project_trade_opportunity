#!/usr/bin/env bash
set -euo pipefail

cd /home/magesh/02_Projects/project_trade_opportunity/backend

echo "=== Alembic current ==="
alembic current

echo
echo "=== Alembic heads ==="
alembic heads

echo
echo "=== SQLAlchemy metadata ==="
python - <<'PY'
from app import models
from app.db.base import Base

print("metadata.schema =", Base.metadata.schema)

for table in sorted(Base.metadata.tables.values(), key=lambda t: t.name):
    print(f"{table.schema}.{table.name}")
PY

echo
echo "=== PostgreSQL tables ==="
python - <<'PY'
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('public', 'trade_opportunity')
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
    """)).all()

for schema, table in rows:
    print(f"{schema}.{table}")
PY

echo
echo "=== PostgreSQL sequences ==="
python - <<'PY'
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT sequence_schema, sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema IN ('public', 'trade_opportunity')
        ORDER BY sequence_schema, sequence_name
    """)).all()

for schema, sequence in rows:
    print(f"{schema}.{sequence}")
PY

echo
echo "=== Alembic version location ==="
python - <<'PY'
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name = 'alembic_version'
    """)).all()

for schema, table in rows:
    print(f"{schema}.{table}")
PY
