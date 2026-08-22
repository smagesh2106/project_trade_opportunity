from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.repositories.hs_version import HSVersionRepository
from app.schemas.hs_version import HSVersionResponse
from app.services.hs_version import HSVersionService


router = APIRouter(
    prefix="/hs-versions",
)


def get_hs_version_service(
    db: Session = Depends(get_db),
) -> HSVersionService:
    repository = HSVersionRepository(db)
    return HSVersionService(repository)


@router.get(
    "",
    response_model=list[HSVersionResponse],
)
def get_hs_versions(
    service: HSVersionService = Depends(get_hs_version_service),
):
    return service.get_all()


@router.get(
    "/{version_id}",
    response_model=HSVersionResponse,
)
def get_hs_version(
    version_id: int,
    service: HSVersionService = Depends(get_hs_version_service),
):
    version = service.get_by_id(version_id)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HS version {version_id} not found",
        )

    return version