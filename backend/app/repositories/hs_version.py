from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HSVersion


class HSVersionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[HSVersion]:
        statement = (
            select(HSVersion)
            .order_by(HSVersion.version)
        )

        return list(self.db.scalars(statement).all())

    def get_by_id(self, version_id: int) -> HSVersion | None:
        statement = select(HSVersion).where(
            HSVersion.id == version_id
        )

        return self.db.scalar(statement)