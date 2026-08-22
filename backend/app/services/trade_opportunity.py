from datetime import date

from app.repositories.country import CountryRepository
from app.repositories.trade_data import TradeDataRepository
from app.schemas.trade_opportunity import (
    TradeOpportunity,
    TradeOpportunityResponse,
)


class TradeOpportunityService:
    def __init__(
        self,
        trade_repository: TradeDataRepository,
        country_repository: CountryRepository,
    ):
        self.trade_repository = trade_repository
        self.country_repository = country_repository

    def find_suppliers(
        self,
        hs_code_id: int,
        hs_code: str,
        hs_description: str,
        target_country_id: int,
        period_start: date,
        period_end: date | None = None,
    ) -> TradeOpportunityResponse:

        results = self.trade_repository.find_supplier_countries(
            hs_code_id=hs_code_id,
            target_country_id=target_country_id,
            period_start=period_start,
            period_end=period_end,
        )

        opportunities: list[TradeOpportunity] = []

        for rank, (country_id, trade_value) in enumerate(
            results,
            start=1,
        ):
            country = self.country_repository.get_by_id(country_id)

            if country is None:
                continue

            opportunities.append(
                TradeOpportunity(
                    rank=rank,
                    country_id=country.id,
                    country_name=country.name,
                    iso2=country.iso2,
                    iso3=country.iso3,
                    trade_value_usd=float(trade_value),
                    period_start=period_start,
                    period_end=period_end,
                )
            )

        return TradeOpportunityResponse(
            hs_code=hs_code,
            hs_description=hs_description,
            period_start=period_start,
            period_end=period_end,
            opportunities=opportunities,
        )
