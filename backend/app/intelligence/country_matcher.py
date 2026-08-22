from app.repositories.country import CountryRepository

from app.schemas.intelligence import (
    CountryMatch,
    ResolvedCountry,
)


class CountryMatcher:
    def __init__(
        self,
        repository: CountryRepository,
    ):
        self.repository = repository

    def match(
        self,
        country_text: str | None,
    ) -> CountryMatch | None:
        if not country_text:
            return None

        country = self.repository.find_by_identifier(country_text)

        if country is None:
            return None

        return CountryMatch(
            country=ResolvedCountry(
                id=country.id,
                iso2=country.iso2,
                iso3=country.iso3,
                name=country.name,
                confidence=1.0,
            ),
            match_type="exact_identifier",
        )
