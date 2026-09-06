from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.ingestion_status import IngestionStatusResponse
from app.services.ingestion_monitoring import IngestionMonitoringService

router = APIRouter(
    prefix="/ingestion",
)


@router.get(
    "/status",
    response_model=IngestionStatusResponse,
)
def get_ingestion_status(
    db: Session = Depends(get_db),
) -> IngestionStatusResponse:
    service = IngestionMonitoringService(db)

    return service.get_status()
