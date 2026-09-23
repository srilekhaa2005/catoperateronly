"""Load the deterministic seed CSVs produced by simulator/seed_data/generate_seed.py.

Usage from backend/:
    python -m app.seed
"""
import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Machine, Operator, Task, TaskTimeLog

SEED_DIR = Path(__file__).resolve().parents[2] / "simulator" / "seed_data"

def _dt(value: str):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def _date(value: str):
    return date.fromisoformat(value)

def _read(name: str):
    with open(SEED_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def seed(db: Session) -> None:
    operators = _read("operators.csv")
    machines = _read("machines.csv")
    tasks = _read("tasks.csv")
    logs = _read("task_time_logs.csv")

    # Idempotent for a fresh/empty schema: skip tables already populated.
    if not db.query(Operator).first():
        db.add_all([
            Operator(
                id=int(r["id"]), name=r["name"], employee_code=r["employee_code"],
                preferred_language=r["preferred_language"], role=r["role"],
                experience_years=Decimal(r["experience_years"]),
            ) for r in operators
        ])

    if not db.query(Machine).first():
        db.add_all([
            Machine(
                id=int(r["id"]), machine_code=r["machine_code"],
                machine_type=r["machine_type"], model=r["model"], status=r["status"],
            ) for r in machines
        ])

    if not db.query(Task).first():
        db.add_all([
            Task(
                id=int(r["id"]), operator_id=int(r["operator_id"]),
                machine_id=int(r["machine_id"]), task_type=r["task_type"],
                site_zone=r["site_zone"] or None,
                weather_condition=r["weather_condition"] or None,
                status=r["status"], scheduled_date=_date(r["scheduled_date"]),
                estimated_duration_minutes=int(r["estimated_duration_minutes"]) if r["estimated_duration_minutes"] else None,
                actual_duration_minutes=int(r["actual_duration_minutes"]) if r["actual_duration_minutes"] else None,
                started_at=_dt(r["started_at"]), completed_at=_dt(r["completed_at"]),
            ) for r in tasks
        ])

    if not db.query(TaskTimeLog).first():
        db.add_all([
            TaskTimeLog(
                id=int(r["id"]), task_type=r["task_type"], machine_type=r["machine_type"],
                site_zone=r["site_zone"] or None, weather_condition=r["weather_condition"] or None,
                operator_experience_years=Decimal(r["operator_experience_years"]) if r["operator_experience_years"] else None,
                duration_minutes=int(r["duration_minutes"]), recorded_date=_date(r["recorded_date"]),
            ) for r in logs
        ])

    db.commit()

    # Explicit seed ids require sequence alignment for subsequent SERIAL inserts.
    if db.bind and db.bind.dialect.name == "postgresql":
        for table in ("operators", "machines", "tasks", "task_time_logs"):
            db.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            ))
        db.commit()

if __name__ == "__main__":
    if not SEED_DIR.exists():
        raise SystemExit(f"Seed directory not found: {SEED_DIR}")
    with SessionLocal() as db:
        seed(db)
    print("Seed data loaded.")
