from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.common import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok", "timestamp": datetime.now(timezone.utc)}
