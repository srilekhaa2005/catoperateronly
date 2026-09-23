from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Alert, MachineReading, Operator
from ..schemas.api import AlertStatusUpdate
from ..services.translation import translate, SUPPORTED_LANGUAGES

router = APIRouter(tags=["alerts"])

def alert_out(a):
    return {"id": a.id, "machine_id": a.machine_id, "task_id": a.task_id, "operator_id": a.operator_id,
            "alert_type": a.alert_type, "severity": a.severity, "status": a.status, "detected_at": a.detected_at}

@router.get("/operators/{operator_id}/alerts")
def operator_alerts(operator_id: int, status: str = "open", limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    if not db.get(Operator, operator_id): raise HTTPException(404, detail=f"Operator with id {operator_id} was not found")
    q = db.query(Alert).filter(Alert.operator_id == operator_id)
    if status: q = q.filter(Alert.status == status)
    return {"alerts": [alert_out(a) for a in q.order_by(Alert.detected_at.desc()).offset(offset).limit(limit).all()]}

@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a: raise HTTPException(404, detail=f"Alert with id {alert_id} was not found")
    data = alert_out(a)
    r = a.reading
    data["reading"] = None if not r else {"engine_temp_c": r.engine_temp_c, "hydraulic_pressure_psi": r.hydraulic_pressure_psi, "anomaly_score": float(r.anomaly_score or 0)}
    return data

@router.get("/alerts/{alert_id}/explain")
def explain_alert(alert_id: int, lang: str = "en", db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a: raise HTTPException(404, detail=f"Alert with id {alert_id} was not found")
    if lang not in SUPPORTED_LANGUAGES: lang = "en"
    if not a.explanation_text or not a.recommended_action:
        templates = {
            "hydraulic_overheat": ("Engine temperature is above the configured safe operating threshold.", "Stop the machine safely and inspect the hydraulic and cooling systems."),
            "seatbelt_unfastened": ("The operator seatbelt is unfastened while the machine is operating.", "Stop the machine safely and fasten the seatbelt before continuing."),
            "proximity_critical": ("A person or obstacle is within the critical proximity zone.", "Stop the machine immediately and verify the area is clear."),
            "proximity_warning": ("A person or obstacle is inside the warning proximity zone.", "Reduce movement and verify the surrounding area before continuing."),
            "low_hydraulic_pressure": ("Hydraulic pressure is below the configured operating range.", "Pause operation and inspect the hydraulic system before continuing."),
            "excessive_idle": ("The machine has been idling for an extended period.", "Stop or resume productive work to reduce unnecessary idling and fuel use."),
            "unusual_vibration": ("Machine vibration is above the configured normal range.", "Pause operation and inspect the machine for abnormal vibration sources."),
            "unusual_machine_usage": ("Machine telemetry differs significantly from the learned normal operating pattern.", "Review the machine state and operating conditions before continuing."),
        }
        a.explanation_text, a.recommended_action = templates.get(a.alert_type, ("An abnormal machine condition was detected.", "Pause operation and inspect the machine before continuing."))
        db.commit(); db.refresh(a)
    explanation, action, fallback = translate(a.alert_type, a.explanation_text, a.recommended_action, lang)
    result = {"alert_id": a.id, "language": "en" if fallback else lang, "explanation": explanation, "recommended_action": action, "source_language": "en"}
    if fallback: result["fallback"] = True
    return result

@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertStatusUpdate, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a: raise HTTPException(404, detail=f"Alert with id {alert_id} was not found")
    valid = {"open", "acknowledged", "resolved"}
    if payload.status not in valid: raise HTTPException(422, detail="Invalid status transition")
    if a.status == "resolved" and payload.status != "resolved": raise HTTPException(422, detail="Invalid status transition")
    from datetime import datetime, timezone
    a.status = payload.status
    if payload.status == "acknowledged": a.acknowledged_at = datetime.now(timezone.utc)
    if payload.status == "resolved":
        if not a.acknowledged_at: a.acknowledged_at = datetime.now(timezone.utc)
        a.resolved_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(a)
    return {"id": a.id, "status": a.status, "acknowledged_at": a.acknowledged_at, "resolved_at": a.resolved_at}

@router.get("/alerts")
def fleet_alerts(status: str = "open", severity: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(Alert)
    if status: q = q.filter(Alert.status == status)
    if severity: q = q.filter(Alert.severity == severity)
    return {"alerts": [alert_out(a) for a in q.order_by(Alert.detected_at.desc()).offset(offset).limit(limit).all()]}
