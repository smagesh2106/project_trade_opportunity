from app.db.session import SessionLocal
from app.ingestion.country_sync import sync_country_master


def main() -> None:
    db = SessionLocal()

    try:
        result = sync_country_master(db)

        print("UN Comtrade country master synchronization completed.")
        print(f"Source records : {result.source_records}")
        print(f"Inserted       : {result.inserted}")
        print(f"Updated        : {result.updated}")
        print(f"Skipped        : {result.skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
