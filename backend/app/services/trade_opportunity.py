from datetime import date

from app.repositories.country import CountryRepository
from app.repositories.trade_data import TradeDataRepository
from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    TradeIntent,
    TradeQuery,
)
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

    def analyze(
        self,
        trade_query: TradeQuery,
    ) -> TradeOpportunityResponse:

        # --------------------------------------------------
        # Validate intent
        # --------------------------------------------------

        if trade_query.intent not in (
            TradeIntent.SUPPLIER_SEARCH,
            TradeIntent.BUYER_SEARCH,
        ):
            raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

        # --------------------------------------------------
        # Product is required
        # --------------------------------------------------

        if trade_query.product is None:
            raise ValueError(
                f"Product could not be resolved from the query: "
                f"{trade_query.original_query}"
            )

        # --------------------------------------------------
        # At least one HS code is required
        # --------------------------------------------------

        if not trade_query.hs_codes:
            raise ValueError("At least one HS code is required for trade analysis.")

        # --------------------------------------------------
        # First version:
        #
        # Use the first resolved HS code.
        #
        # Later we can support multiple HS mappings and
        # aggregate the results.
        # --------------------------------------------------

        hs_code = trade_query.hs_codes[0]

        # --------------------------------------------------
        # First version uses the 2025 analysis period.
        #
        # Later this will come from TradeQuery when we add
        # natural-language period extraction.
        # --------------------------------------------------

        period_start = date(2025, 1, 1)
        period_end = date(2025, 12, 31)

        # ==================================================
        # SUPPLIER SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.SUPPLIER_SEARCH:

            results = self._analyze_supplier_search(
                trade_query=trade_query,
                hs_code_id=hs_code.id,
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # BUYER SEARCH
        # ==================================================

        elif trade_query.intent == TradeIntent.BUYER_SEARCH:

            results = self._analyze_buyer_search(
                trade_query=trade_query,
                hs_code_id=hs_code.id,
                period_start=period_start,
                period_end=period_end,
            )

        else:
            raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

        # ==================================================
        # Convert repository results into business results
        # ==================================================

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
            hs_code=hs_code.code,
            hs_description=hs_code.description,
            period_start=period_start,
            period_end=period_end,
            opportunities=opportunities,
        )

    # ======================================================
    # SUPPLIER SEARCH
    # ======================================================

    def _analyze_supplier_search(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # --------------------------------------------------
        # Specific country
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.SPECIFIC:

            if trade_query.country is None:
                raise ValueError("Country is required for specific country searches.")

            # --------------------------------------------------
            # LOCATION
            #
            # Example:
            #
            # "Find suppliers of electrical panels in India"
            #
            # This means suppliers located in India.
            #
            # Our current trade_data model contains
            # country-to-country trade flows, not supplier
            # company locations.
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.LOCATION:
                raise ValueError(
                    "Supplier location searches are not yet "
                    "supported by the trade data model. "
                    "The current dataset contains "
                    "country-to-country trade flows, "
                    "not supplier company locations."
                )

            # --------------------------------------------------
            # DESTINATION
            #
            # Example:
            #
            # "Find suppliers of electrical panels to India"
            #
            # India = importing/destination country.
            #
            # Find countries supplying India.
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.DESTINATION:

                return self.trade_repository.find_supplier_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # ORIGIN
            #
            # Example:
            #
            # "Find suppliers of electrical panels from India"
            #
            # This describes suppliers originating from India.
            #
            # Our current supplier-search semantics do not yet
            # support this as a separate operation.
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.ORIGIN:
                raise ValueError(
                    "Origin-based supplier searches are not "
                    "yet supported for supplier_search."
                )

            raise ValueError(
                f"Unsupported country role: " f"{trade_query.country_role.value}"
            )

        # --------------------------------------------------
        # All countries
        #
        # Example:
        #
        # "Find suppliers of electrical panels"
        #
        # Find countries exporting the product globally.
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.ALL:

            return self.trade_repository.find_global_supplier_countries(
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(
            f"Unsupported country scope: " f"{trade_query.country_scope.value}"
        )

    # ======================================================
    # BUYER SEARCH
    # ======================================================

    def _analyze_buyer_search(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # --------------------------------------------------
        # Specific country
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.SPECIFIC:

            if trade_query.country is None:
                raise ValueError("Country is required for specific country searches.")

            # --------------------------------------------------
            # LOCATION
            #
            # Example:
            #
            # "Who imports electrical panels in India?"
            #
            # India = buyer/importer location.
            #
            # The current trade data can tell us India's
            # import activity, but cannot identify individual
            # importer companies.
            #
            # Therefore the result is country-level import
            # activity.
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.LOCATION:

                return self.trade_repository.find_buyer_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # DESTINATION
            #
            # Example:
            #
            # "Who imports electrical panels to India?"
            #
            # India = destination/importing country.
            #
            # At the country-level data layer this is
            # equivalent to the specific buyer country.
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.DESTINATION:

                return self.trade_repository.find_buyer_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # ORIGIN
            #
            # Example:
            #
            # "Who buys electrical panels from India?"
            #
            # India = origin/exporting country.
            #
            # Find the countries importing from India.
            #
            # Repository method:
            #
            # find_buyer_countries_from_origin()
            #
            # reporter_country = India
            # partner_country  = buyer
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.ORIGIN:

                return self.trade_repository.find_buyer_countries_from_origin(
                    hs_code_id=hs_code_id,
                    origin_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            raise ValueError(
                f"Unsupported country role: " f"{trade_query.country_role.value}"
            )

        # --------------------------------------------------
        # All countries
        #
        # Example:
        #
        # "Who imports electrical panels?"
        #
        # Find countries importing the product globally.
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.ALL:

            return self.trade_repository.find_global_buyer_countries(
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(
            f"Unsupported country scope: " f"{trade_query.country_scope.value}"
        )
