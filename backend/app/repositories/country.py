from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Country


class CountryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Country]:
        statement = (
            select(Country).where(Country.active.is_(True)).order_by(Country.name)
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

    def find_by_identifier(
        self,
        value: str,
    ) -> Country | None:
        normalized_value = value.strip().lower()

        statement = select(Country).where(
            Country.active.is_(True),
            or_(
                func.lower(Country.name) == normalized_value,
                func.lower(Country.iso2) == normalized_value,
                func.lower(Country.iso3) == normalized_value,
            ),
        )

        return self.db.execute(statement).scalar_one_or_none()
