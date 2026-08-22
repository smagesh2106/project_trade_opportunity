from app.models import Country
from app.repositories.country import CountryRepository


class CountryService:
    def __init__(self, repository: CountryRepository):
        self.repository = repository

    def get_all(self) -> list[Country]:
        return self.repository.get_all()

    def get_by_id(self, country_id: int) -> Country | None:
        return self.repository.get_by_id(country_id)

    def get_by_iso3(self, iso3: str) -> Country | None:
        return self.repository.get_by_iso3(iso3)