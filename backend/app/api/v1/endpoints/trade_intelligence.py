from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.intelligence.country_matcher import CountryMatcher
from app.intelligence.hs_resolver import HSResolver
from app.intelligence.product_matcher import ProductMatcher
from app.intelligence.trade_query_builder import TradeQueryBuilder

from app.repositories.country import CountryRepository
from app.repositories.product import ProductRepository
from app.repositories.trade_data import TradeDataRepository

from app.schemas.trade_opportunity import TradeOpportunityResponse

from app.services.openai_service import OpenAIService
from app.services.trade_intelligence import TradeIntelligenceService
from app.services.trade_opportunity import TradeOpportunityService

router = APIRouter(
    prefix="/trade",
)


class TradeAnalysisRequest(BaseModel):
    query: str


def get_trade_intelligence_service(
    db: Session = Depends(get_db),
) -> TradeIntelligenceService:

    # ==================================================
    # Repositories
    # ==================================================

    product_repository = ProductRepository(db)

    country_repository = CountryRepository(db)

    trade_repository = TradeDataRepository(db)

    # ==================================================
    # Intelligence components
    # ==================================================

    product_matcher = ProductMatcher(product_repository)

    country_matcher = CountryMatcher(country_repository)

    hs_resolver = HSResolver()

    trade_query_builder = TradeQueryBuilder(
        product_matcher=product_matcher,
        country_matcher=country_matcher,
        hs_resolver=hs_resolver,
    )

    # ==================================================
    # Services
    # ==================================================

    openai_service = OpenAIService()

    trade_opportunity_service = TradeOpportunityService(
        trade_repository=trade_repository,
        country_repository=country_repository,
    )

    # ==================================================
    # Complete Trade Intelligence service
    # ==================================================

    return TradeIntelligenceService(
        openai_service=openai_service,
        trade_query_builder=trade_query_builder,
        trade_opportunity_service=trade_opportunity_service,
    )


@router.post(
    "/analyze",
    response_model=TradeOpportunityResponse,
)
def analyze_trade(
    request: TradeAnalysisRequest,
    service: TradeIntelligenceService = Depends(get_trade_intelligence_service),
):
    # ==================================================
    # Validate request
    # ==================================================

    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade query cannot be empty.",
        )

    # ==================================================
    # Execute trade intelligence
    # ==================================================

    try:

        return service.analyze(request.query)

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
