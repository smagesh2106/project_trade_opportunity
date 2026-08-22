from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HSCode


class HSCodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        hs_version_id: int | None = None,
        level: int | None = None,
        parent_id: int | None = None,
    ) -> list[HSCode]:

        statement = select(HSCode).where(HSCode.active.is_(True))

        if hs_version_id is not None:
            statement = statement.where(HSCode.hs_version_id == hs_version_id)

        if level is not None:
            statement = statement.where(HSCode.level == level)

        if parent_id is not None:
            statement = statement.where(HSCode.parent_id == parent_id)

        statement = statement.order_by(HSCode.code)

        return list(self.db.scalars(statement).all())

    def get_by_id(
        self,
        hs_code_id: int,
    ) -> HSCode | None:

        statement = select(HSCode).where(
            HSCode.id == hs_code_id,
            HSCode.active.is_(True),
        )

        return self.db.scalar(statement)

    def get_by_code(
        self,
        code: str,
        hs_version_id: int | None = None,
    ) -> HSCode | None:

        statement = select(HSCode).where(
            HSCode.code == code,
            HSCode.active.is_(True),
        )

        if hs_version_id is not None:
            statement = statement.where(HSCode.hs_version_id == hs_version_id)

        return self.db.scalar(statement)
