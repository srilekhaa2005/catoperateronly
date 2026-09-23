from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Incident, Operator, Machine, Alert
from ..schemas.api import IncidentCreate

router = APIRouter(tags=["incidents"])

@router.post("/incidents", status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    if not db.get(Operator, payload.operator_id): raise HTTPException(404, detail="Operator not found")
    if not db.get(Machine, payload.machine_id): raise HTTPException(404, detail="Machine not found")
    if payload.alert_id is not None and not db.get(Alert, payload.alert_id): raise HTTPException(404, detail="Alert not found")
    if payload.severity not in {"info", "warning", "critical"}: raise HTTPException(422, detail="Invalid severity")
    row = Incident(**payload.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "operator_id": row.operator_id, "machine_id": row.machine_id, "alert_id": row.alert_id,
            "description": row.description, "severity": row.severity, "created_at": row.created_at}

@router.get("/operators/{operator_id}/incidents")
def list_incidents(operator_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    if not db.get(Operator, operator_id): raise HTTPException(404, detail="Operator not found")
    rows = db.query(Incident).filter(Incident.operator_id == operator_id).order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    return {"incidents": [{"id": r.id, "operator_id": r.operator_id, "machine_id": r.machine_id, "alert_id": r.alert_id,
                            "description": r.description, "severity": r.severity, "created_at": r.created_at} for r in rows]}
