from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.hs_code import HSCodeRepository
from app.schemas.hs_code import HSCodeResponse
from app.services.hs_code import HSCodeService


router = APIRouter(
    prefix="/hs-codes",
)


def get_hs_code_service(
    db: Session = Depends(get_db),
) -> HSCodeService:
    repository = HSCodeRepository(db)
    return HSCodeService(repository)


@router.get(
    "",
    response_model=list[HSCodeResponse],
)
def get_hs_codes(
    hs_version_id: int | None = Query(default=None),
    level: int | None = Query(
        default=None,
        ge=1,
    ),
    parent_id: int | None = Query(
        default=None,
        ge=1,
    ),
    service: HSCodeService = Depends(get_hs_code_service),
):
    return service.get_all(
        hs_version_id=hs_version_id,
        level=level,
        parent_id=parent_id,
    )


@router.get(
    "/{hs_code_id}",
    response_model=HSCodeResponse,
)
def get_hs_code(
    hs_code_id: int,
    service: HSCodeService = Depends(get_hs_code_service),
):
    hs_code = service.get_by_id(hs_code_id)

    if hs_code is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HS code {hs_code_id} not found",
        )

    return hs_code