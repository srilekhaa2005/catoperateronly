from functools import lru_cache
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import TaskTimeLog

MODEL_VERSION = "task_time_v1"

@lru_cache(maxsize=1)
def _feature_maps():
    return {}, {}


def predict_duration(db: Session, *, task_type: str, machine_type: str, site_zone: str | None,
                     weather_condition: str | None, operator_experience_years: float | None) -> tuple[int, float]:
    rows = db.query(TaskTimeLog).all()
    if len(rows) >= 5:
        cats = {}
        for col in ("task_type", "machine_type", "site_zone", "weather_condition"):
            cats[col] = {v: i for i, v in enumerate(sorted({getattr(r, col) or "unknown" for r in rows}))}
        X, y = [], []
        for r in rows:
            X.append([
                cats["task_type"].get(r.task_type, 0),
                cats["machine_type"].get(r.machine_type, 0),
                cats["site_zone"].get(r.site_zone or "unknown", 0),
                cats["weather_condition"].get(r.weather_condition or "unknown", 0),
                float(r.operator_experience_years or 0),
            ])
            y.append(r.duration_minutes)
        model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=2)
        model.fit(np.asarray(X), np.asarray(y))
        x = [[
            cats["task_type"].get(task_type, 0), cats["machine_type"].get(machine_type, 0),
            cats["site_zone"].get(site_zone or "unknown", 0),
            cats["weather_condition"].get(weather_condition or "unknown", 0),
            float(operator_experience_years or 0),
        ]]
        return max(1, round(float(model.predict(x)[0]))), float(np.mean(y))

    # Contract-mandated historical fallback chain.
    q = db.query(func.avg(TaskTimeLog.duration_minutes)).filter(
        TaskTimeLog.task_type == task_type, TaskTimeLog.machine_type == machine_type
    ).scalar()
    if q is None:
        q = db.query(func.avg(TaskTimeLog.duration_minutes)).filter(TaskTimeLog.task_type == task_type).scalar()
    if q is None:
        q = db.query(func.avg(TaskTimeLog.duration_minutes)).scalar()
    if q is None:
        q = 60
    return max(1, round(float(q))), float(q)
