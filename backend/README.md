# Fresh Trade Opportunity PostgreSQL schema

This is the clean Option A setup for the development database.

PostgreSQL database:
    the database configured by POSTGRES_DB

Application schema:
    trade_opportunity

The existing Alembic revision chain is preserved:

    01d0c2f4ab77
        -> 768dac678df8
        -> 195941c088e6
        -> f4af954581bd
        -> b61f7a7282d3

No temporary "move tables" migration is needed for a fresh database.

## Why historical migrations remain unchanged

The Alembic environment sets:

    search_path = trade_opportunity, public

during migration execution, while `alembic_version` is explicitly stored in
public. Therefore the existing historical migrations can continue using
unqualified table names and still create/modify the application's tables in
trade_opportunity.

SQLAlchemy Base.metadata also uses trade_opportunity explicitly.

## Install

Copy:
    app/db/base.py
    app/db/migrations/env.py
    app/db/migrations/versions/01d0c2f4ab77_initial_migration.py

Delete:
    app/db/migrations/versions/a9f4c2d7e1b3_move_trade_tables_to_trade_opportunity.py

if that temporary migration is present.

## Reset the development database

IMPORTANT: This deletes the PostgreSQL development volume.

    ./reset_dev_database.sh

The script requires typing:

    RESET-DEV-DB

before it will proceed.

## Verify

    ./verify_trade_schema.sh

Expected application tables and sequences are under:

    trade_opportunity

The Alembic version table is under:

    public
