from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Machine, MachineReading, Task
from ..schemas.api import MachineEvent, ScenarioRequest
from ..services.anomaly import score_reading
from ..services.safety import evaluate_safety

router = APIRouter(tags=["machines"])

@router.post("/machine-events", status_code=201)
def ingest_machine_event(payload: MachineEvent, db: Session = Depends(get_db)):
    machine = db.get(Machine, payload.machine_id)
    if not machine: raise HTTPException(404, detail=f"Machine with id {payload.machine_id} was not found")
    if payload.task_id is not None and not db.get(Task, payload.task_id):
        raise HTTPException(404, detail=f"Task with id {payload.task_id} was not found")
    data = payload.model_dump()
    score, anomaly = score_reading(data)
    safety = evaluate_safety(data)
    reading = MachineReading(machine_id=payload.machine_id, task_id=payload.task_id, recorded_at=payload.recorded_at,
        engine_temp_c=payload.engine_temp_c, hydraulic_pressure_psi=payload.hydraulic_pressure_psi,
        fuel_level_pct=payload.fuel_level_pct, rpm=payload.rpm, idle_time_seconds=payload.idle_time_seconds,
        vibration_level=payload.vibration_level, load_weight_kg=payload.load_weight_kg, ambient_temp_c=payload.ambient_temp_c,
        seatbelt_status=payload.seatbelt_status, proximity_distance_m=payload.proximity_distance_m,
        safety_alert_triggered=bool(safety), is_simulated=payload.is_simulated, anomaly_score=score, is_anomaly=anomaly)
    db.add(reading); db.flush()
    operator_id = None
    if payload.task_id is not None:
        task = db.get(Task, payload.task_id); operator_id = task.operator_id if task else None
    alerts = []
    for item in safety:
        alert = __import__('app.models', fromlist=['Alert']).Alert(machine_id=payload.machine_id, task_id=payload.task_id,
            operator_id=operator_id, reading_id=reading.id, alert_type=item.alert_type, severity=item.severity,
            explanation_text=item.explanation, recommended_action=item.action)
        db.add(alert); alerts.append(alert)
    if anomaly and not safety:
        from ..models import Alert
        alert = Alert(machine_id=payload.machine_id, task_id=payload.task_id, operator_id=operator_id,
                      reading_id=reading.id, alert_type="unusual_machine_usage", severity="warning",
                      explanation_text="Machine telemetry differs significantly from the learned normal operating pattern.",
                      recommended_action="Review the machine state and operating conditions before continuing.")
        db.add(alert); alerts.append(alert)
    db.commit()
    return {"reading_id": reading.id, "machine_id": reading.machine_id, "is_anomaly": reading.is_anomaly,
            "anomaly_score": float(reading.anomaly_score or 0), "safety_alert_triggered": reading.safety_alert_triggered,
            "alerts_created": len(alerts)}

@router.get("/machines/{machine_id}/readings/latest")
def latest_readings(machine_id: int, count: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    if not db.get(Machine, machine_id): raise HTTPException(404, detail=f"Machine with id {machine_id} was not found")
    rows = db.query(MachineReading).filter(MachineReading.machine_id == machine_id).order_by(MachineReading.recorded_at.desc()).limit(count).all()
    rows.reverse()
    return {"machine_id": machine_id, "readings": [
        {"id": r.id, "recorded_at": r.recorded_at, "engine_temp_c": r.engine_temp_c,
         "hydraulic_pressure_psi": r.hydraulic_pressure_psi, "fuel_level_pct": r.fuel_level_pct,
         "rpm": r.rpm, "idle_time_seconds": r.idle_time_seconds, "vibration_level": r.vibration_level,
         "load_weight_kg": r.load_weight_kg, "ambient_temp_c": r.ambient_temp_c,
         "seatbelt_status": r.seatbelt_status, "proximity_distance_m": r.proximity_distance_m,
         "is_anomaly": r.is_anomaly, "anomaly_score": float(r.anomaly_score or 0)} for r in rows]}

@router.get("/machines")
def list_machines(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    rows = db.query(Machine).order_by(Machine.id).offset(offset).limit(limit).all()
    return {"machines": [{"id": m.id, "machine_code": m.machine_code, "machine_type": m.machine_type, "model": m.model, "status": m.status} for m in rows]}

@router.post("/simulator/scenario")
def start_scenario(payload: ScenarioRequest, db: Session = Depends(get_db)):
    from ..services.simulator_scenarios import SCENARIO_NAMES
    if payload.scenario not in SCENARIO_NAMES: raise HTTPException(422, detail=f"Unknown scenario: {payload.scenario}")
    if not db.get(Machine, payload.machine_id): raise HTTPException(404, detail=f"Machine with id {payload.machine_id} was not found")
    return {"status": "scenario_started", "machine_id": payload.machine_id, "scenario": payload.scenario}
