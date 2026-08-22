from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

router = APIRouter()


@router.get("/db")
def database_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    value = result.scalar_one()

    return {
        "status": "healthy",
        "database": "postgresql",
        "test": value,
    }
