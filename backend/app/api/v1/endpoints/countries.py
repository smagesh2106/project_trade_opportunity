from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.country import CountryRepository
from app.schemas.country import CountryResponse
from app.services.country import CountryService

router = APIRouter(
    prefix="/countries",
)


def get_country_service(
    db: Session = Depends(get_db),
) -> CountryService:
    repository = CountryRepository(db)
    return CountryService(repository)


@router.get(
    "",
    response_model=list[CountryResponse],
)
def get_countries(
    service: CountryService = Depends(get_country_service),
):
    return service.get_all()


@router.get(
    "/{country_id}",
    response_model=CountryResponse,
)
def get_country(
    country_id: int,
    service: CountryService = Depends(get_country_service),
):
    country = service.get_by_id(country_id)

    if country is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country {country_id} not found",
        )

    return country
