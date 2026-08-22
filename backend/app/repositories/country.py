from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Country


class CountryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Country]:
        statement = (
            select(Country)
            .where(Country.active.is_(True))
            .order_by(Country.name)
        )

        return list(self.db.scalars(statement).all())

    def get_by_id(self, country_id: int) -> Country | None:
        statement = select(Country).where(
            Country.id == country_id,
            Country.active.is_(True),
        )

        return self.db.scalar(statement)

    def get_by_iso3(self, iso3: str) -> Country | None:
        statement = select(Country).where(
            Country.iso3 == iso3.upper(),
            Country.active.is_(True),
        )

        return self.db.scalar(statement)