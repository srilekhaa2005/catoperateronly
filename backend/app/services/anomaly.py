from functools import lru_cache
import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = [
    "engine_temp_c", "hydraulic_pressure_psi", "fuel_level_pct", "rpm",
    "idle_time_seconds", "vibration_level", "load_weight_kg", "ambient_temp_c",
]

NORMAL_MEAN = np.array([92.0, 2450.0, 60.0, 1750.0, 20.0, 1.1, 3000.0, 32.0])
NORMAL_SCALE = np.array([8.0, 450.0, 20.0, 300.0, 120.0, 0.6, 1800.0, 8.0])

@lru_cache(maxsize=1)
def get_model() -> IsolationForest:
    rng = np.random.default_rng(42)
    X = rng.normal(NORMAL_MEAN, NORMAL_SCALE, size=(500, len(FEATURES)))
    X[:, 0] = np.clip(X[:, 0], 70, 109)
    X[:, 1] = np.clip(X[:, 1], 1200, 3400)
    X[:, 2] = np.clip(X[:, 2], 5, 100)
    X[:, 4] = np.clip(X[:, 4], 0, 1800)
    X[:, 5] = np.clip(X[:, 5], 0, 5)
    model = IsolationForest(n_estimators=150, contamination=0.05, random_state=42)
    model.fit(X)
    return model


def score_reading(data: dict) -> tuple[float, bool]:
    values = []
    for name, mean, scale in zip(FEATURES, NORMAL_MEAN, NORMAL_SCALE):
        value = data.get(name)
        values.append(float(mean if value is None else value))
    x = np.asarray([values], dtype=float)
    model = get_model()
    raw = float(model.decision_function(x)[0])
    # Convert IsolationForest decision function to a bounded, UI-friendly score.
    score = max(0.0, min(1.0, 0.5 - raw))
    return round(score, 4), bool(model.predict(x)[0] == -1)
