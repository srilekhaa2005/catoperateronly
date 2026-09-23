from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "te", "kn"}

class OperatorLanguageUpdate(BaseModel):
    preferred_language: str

class ScenarioRequest(BaseModel):
    machine_id: int
    scenario: str
    duration_seconds: int = Field(default=60, ge=1, le=3600)

class MachineEvent(BaseModel):
    machine_id: int
    task_id: int | None = None
    recorded_at: datetime
    engine_temp_c: float | None = None
    hydraulic_pressure_psi: float | None = None
    fuel_level_pct: float | None = None
    rpm: int | None = None
    idle_time_seconds: int | None = Field(default=None, ge=0)
    vibration_level: float | None = None
    load_weight_kg: float | None = None
    ambient_temp_c: float | None = None
    seatbelt_status: bool | None = None
    proximity_distance_m: float | None = Field(default=None, ge=0)
    is_simulated: bool = True

class AlertStatusUpdate(BaseModel):
    status: str

class IncidentCreate(BaseModel):
    operator_id: int
    machine_id: int
    alert_id: int | None = None
    description: str
    severity: str

class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
