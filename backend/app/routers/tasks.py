from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Operator, Task, TaskTimeLog
from ..services.prediction import predict_duration, MODEL_VERSION

router = APIRouter(tags=["tasks"])

def task_out(t, include_operator=False):
    d = {"id": t.id, "task_type": t.task_type, "site_zone": t.site_zone, "status": t.status,
         "scheduled_date": t.scheduled_date.isoformat(), "estimated_duration_minutes": t.estimated_duration_minutes,
         "actual_duration_minutes": t.actual_duration_minutes,
         "machine": {"id": t.machine.id, "machine_code": t.machine.machine_code,
                     "machine_type": t.machine.machine_type, "model": t.machine.model}}
    if include_operator:
        d["operator"] = {"id": t.operator.id, "name": t.operator.name, "employee_code": t.operator.employee_code}
    return d

@router.get("/operators/{operator_id}/tasks")
def operator_tasks(operator_id: int, date_: date | None = Query(None, alias="date"), limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    if not db.get(Operator, operator_id): raise HTTPException(404, detail=f"Operator with id {operator_id} was not found")
    target = date_ or datetime.now(timezone.utc).date()
    rows = db.query(Task).filter(Task.operator_id == operator_id, Task.scheduled_date == target).order_by(Task.id).offset(offset).limit(limit).all()
    return {"tasks": [task_out(t) for t in rows]}

@router.post("/tasks/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t: raise HTTPException(404, detail=f"Task with id {task_id} was not found")
    if t.status in ("in_progress", "completed"): raise HTTPException(400, detail="Task already in progress or completed")
    t.status = "in_progress"; t.started_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(t)
    return {"id": t.id, "status": t.status, "started_at": t.started_at}

@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t: raise HTTPException(404, detail=f"Task with id {task_id} was not found")
    if t.status != "in_progress": raise HTTPException(400, detail="Task not currently in progress")
    now = datetime.now(timezone.utc); t.completed_at = now; t.status = "completed"
    t.actual_duration_minutes = max(1, round((now - t.started_at).total_seconds() / 60)) if t.started_at else None
    db.add(TaskTimeLog(task_type=t.task_type, machine_type=t.machine.machine_type, site_zone=t.site_zone,
                       weather_condition=t.weather_condition, operator_experience_years=t.operator.experience_years,
                       duration_minutes=t.actual_duration_minutes or 1, recorded_date=now.date()))
    db.commit(); db.refresh(t)
    return {"id": t.id, "status": t.status, "actual_duration_minutes": t.actual_duration_minutes, "completed_at": t.completed_at}

@router.get("/tasks/{task_id}/estimate")
def estimate_task(task_id: int, db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if not t: raise HTTPException(404, detail=f"Task with id {task_id} was not found")
    pred, hist = predict_duration(db, task_type=t.task_type, machine_type=t.machine.machine_type, site_zone=t.site_zone,
                                  weather_condition=t.weather_condition, operator_experience_years=float(t.operator.experience_years or 0))
    t.estimated_duration_minutes = pred; db.commit()
    return {"task_id": t.id, "estimated_duration_minutes": pred, "model_version": MODEL_VERSION,
            "inputs_used": {"task_type": t.task_type, "machine_type": t.machine.machine_type, "site_zone": t.site_zone,
                             "weather_condition": t.weather_condition, "operator_experience_years": float(t.operator.experience_years or 0),
                             "historical_avg_duration_minutes": round(hist, 2)}}

@router.get("/tasks")
def all_tasks(date_: date | None = Query(None, alias="date"), limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    target = date_ or datetime.now(timezone.utc).date()
    rows = db.query(Task).filter(Task.scheduled_date == target).order_by(Task.id).offset(offset).limit(limit).all()
    return {"tasks": [task_out(t, True) for t in rows]}
