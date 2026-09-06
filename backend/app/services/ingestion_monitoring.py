from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DataSource, IngestionRun
from app.schemas.ingestion_status import IngestionStatusResponse


class IngestionMonitoringService:
    """Provides a simple summary of the latest ingestion state."""

    def __init__(self, db: Session):
        self.db = db

    def get_status(self) -> IngestionStatusResponse:
        statement = (
            select(IngestionRun, DataSource.name)
            .join(DataSource, DataSource.id == IngestionRun.source_id)
            .order_by(IngestionRun.started_at.desc())
            .limit(1)
        )

        result = self.db.execute(statement).first()

        if result is None:
            return IngestionStatusResponse(
                status="not_available",
                source=None,
                last_run_id=None,
                last_run_status=None,
            )

        run, source_name = result

        if run.status in {"completed", "completed_with_rejections"}:
            overall_status = "healthy"
        elif run.status == "running":
            overall_status = "running"
        else:
            overall_status = "unhealthy"

        latest_period = None

        if run.data_period_start is not None:
            latest_period = str(run.data_period_start.year)

        return IngestionStatusResponse(
            status=overall_status,
            source=source_name,
            last_run_id=run.id,
            last_run_status=run.status,
            last_run_started_at=run.started_at,
            last_run_completed_at=run.completed_at,
            latest_data_period=latest_period,
            records_received=run.records_received,
            records_inserted=run.records_inserted,
            records_updated=run.records_updated,
            records_rejected=run.records_rejected,
            error_message=run.error_message,
        )
