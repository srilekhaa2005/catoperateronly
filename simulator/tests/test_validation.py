"""
test_validation.py — validation for Member 3's deliverable only.

Two things are checked:
  1. Seed data shape: every CSV matches DATABASE_DESIGN.md's columns/types/
     constraints (FKs resolve, enums are in-range, required fields non-null).
  2. Simulator output shape: readings produced by MachineState/scenarios and
     the payload sent to POST /machine-events match API_CONTRACT.md §3.1
     exactly (field names/types), and the /simulator/scenario control
     endpoint validates input per §3.3 (200 on known scenario + valid
     machine, 422 on unknown scenario, 404 on unknown machine).

This does NOT stand up a real backend — it uses FastAPI's TestClient against
this simulator's own app (in dry-run mode, so no network calls happen) purely
to confirm the simulator's contract-facing behavior. Detection logic, DB
writes, and ML scoring are explicitly out of scope (Member 1's code) and are
not exercised here.

Run: `pytest tests/ -v` from the simulator/ directory.
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from machine_state import MachineState  # noqa: E402
from scenarios import SCENARIO_NAMES, apply_scenario, is_known_scenario  # noqa: E402
from simulate import create_app, load_seed_state  # noqa: E402

SEED_DIR = Path(__file__).parent.parent / "seed_data"

MACHINE_TYPES = {"excavator", "dozer", "loader", "grader"}
TASK_STATUSES = {"assigned", "in_progress", "completed", "cancelled"}
WEATHER_CONDITIONS = {"clear", "rain", "extreme_heat", "overcast", "wind"}
OPERATOR_ROLES = {"operator", "supervisor"}
MACHINE_STATUSES = {"idle", "active", "maintenance", "offline"}

READING_FIELDS = {
    "machine_id": int, "task_id": (int, type(None)), "recorded_at": str,
    "engine_temp_c": (int, float), "hydraulic_pressure_psi": (int, float),
    "fuel_level_pct": (int, float), "rpm": int, "idle_time_seconds": int,
    "vibration_level": (int, float), "load_weight_kg": (int, float),
    "ambient_temp_c": (int, float), "seatbelt_status": bool,
    "proximity_distance_m": (int, float), "is_simulated": bool,
}


def read_csv(name):
    with open(SEED_DIR / name) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# 1. Seed data validation
# ---------------------------------------------------------------------------

def test_operators_shape():
    rows = read_csv("operators.csv")
    assert len(rows) > 0
    ids = set()
    codes = set()
    for r in rows:
        assert r["employee_code"] not in codes, "duplicate employee_code"
        codes.add(r["employee_code"])
        ids.add(int(r["id"]))
        assert r["role"] in OPERATOR_ROLES
        assert r["name"].strip() != ""
        exp = float(r["experience_years"])
        assert 0 <= exp <= 50
    assert ids == set(range(1, len(rows) + 1)), "operator ids must be contiguous from 1"


def test_machines_shape():
    rows = read_csv("machines.csv")
    assert len(rows) > 0
    codes = set()
    for r in rows:
        assert r["machine_code"] not in codes, "duplicate machine_code"
        codes.add(r["machine_code"])
        assert r["machine_type"] in MACHINE_TYPES
        assert r["status"] in MACHINE_STATUSES
        assert r["model"].strip() != ""


def test_tasks_shape_and_fks():
    operators = {int(r["id"]) for r in read_csv("operators.csv")}
    machines = {int(r["id"]) for r in read_csv("machines.csv")}
    rows = read_csv("tasks.csv")
    assert len(rows) > 0
    ids = set()
    for r in rows:
        ids.add(int(r["id"]))
        assert int(r["operator_id"]) in operators, "task references unknown operator"
        assert int(r["machine_id"]) in machines, "task references unknown machine"
        assert r["status"] in TASK_STATUSES
        if r["weather_condition"]:
            assert r["weather_condition"] in WEATHER_CONDITIONS
        assert int(r["estimated_duration_minutes"]) > 0
        if r["status"] == "completed":
            assert r["actual_duration_minutes"] not in ("", None), \
                "completed task must have actual_duration_minutes"
            assert r["started_at"] and r["completed_at"]
        if r["status"] == "in_progress":
            assert r["started_at"], "in_progress task must have started_at"
    assert ids == set(range(1, len(rows) + 1)), "task ids must be contiguous from 1"

    in_progress = [r for r in rows if r["status"] == "in_progress"]
    assert len(in_progress) >= 1, "need at least one in_progress task for the simulator to stream against"


def test_task_time_logs_shape_and_fallback_coverage():
    rows = read_csv("task_time_logs.csv")
    assert len(rows) >= 50, "need enough history for the regression model's fallback chain to be meaningful"
    task_types = set()
    for r in rows:
        assert r["machine_type"] in MACHINE_TYPES
        task_types.add(r["task_type"])
        assert r["weather_condition"] in WEATHER_CONDITIONS
        assert int(r["duration_minutes"]) > 0
        exp = r["operator_experience_years"]
        if exp:
            assert 0 <= float(exp) <= 50

    # Fallback-chain sanity: every (task_type, machine_type) pair that appears
    # in tasks.csv should have at least one task_time_logs row for that
    # task_type, so step 2 of the locked fallback (PROJECT_PLAN.md §6a) never
    # has to fall through to the global mean for a task_type we actually use.
    used_task_types = {r["task_type"] for r in read_csv("tasks.csv")}
    missing = used_task_types - task_types
    assert not missing, f"task_time_logs has no history at all for: {missing}"


# ---------------------------------------------------------------------------
# 2. Simulator output validation
# ---------------------------------------------------------------------------

def test_reading_matches_contract_shape():
    state = MachineState(machine_id=1, machine_type="excavator", task_id=101,
                          weather_condition="clear", is_task_active=True, sim_seed=42)
    reading = state.next_reading("2026-09-23T09:15:03Z")
    assert set(reading.keys()) == set(READING_FIELDS.keys()), "reading has extra/missing fields vs API_CONTRACT.md §3.1"
    for field, types in READING_FIELDS.items():
        assert isinstance(reading[field], types), f"{field} has wrong type: {type(reading[field])}"
    assert reading["is_simulated"] is True
    assert 0 <= reading["fuel_level_pct"] <= 100


def test_reading_is_deterministic_given_same_seed():
    s1 = MachineState(machine_id=5, machine_type="dozer", task_id=None,
                       weather_condition="rain", is_task_active=False, sim_seed=42)
    s2 = MachineState(machine_id=5, machine_type="dozer", task_id=None,
                       weather_condition="rain", is_task_active=False, sim_seed=42)
    for _ in range(5):
        r1 = s1.next_reading("2026-09-23T09:00:00Z")
        r2 = s2.next_reading("2026-09-23T09:00:00Z")
        assert r1 == r2, "same seed must reproduce identical reading sequence"


@pytest.mark.parametrize("scenario", SCENARIO_NAMES)
def test_every_declared_scenario_applies_without_error(scenario):
    state = MachineState(machine_id=2, machine_type="loader", task_id=201,
                          weather_condition="clear", is_task_active=True, sim_seed=42)
    state.start_scenario(scenario, duration_seconds=30, interval_seconds=5)
    reading = state.next_reading("2026-09-23T09:00:00Z")
    for field, types in READING_FIELDS.items():
        assert isinstance(reading[field], types)


def test_locked_safety_thresholds_are_reachable():
    """Confirm each scenario that's supposed to breach a locked safety
    threshold (DATABASE_DESIGN.md machine_readings notes) actually produces
    a value on the correct side of that threshold."""
    rng_state = MachineState(machine_id=3, machine_type="excavator", task_id=301,
                              weather_condition="clear", is_task_active=True, sim_seed=42)

    reading = {"proximity_distance_m": 10.0, "seatbelt_status": True}
    apply_scenario(reading, "seatbelt_unfastened", rng_state._rng)
    assert reading["seatbelt_status"] is False

    reading = {"proximity_distance_m": 10.0}
    apply_scenario(reading, "proximity_warning", rng_state._rng)
    assert 2.0 <= reading["proximity_distance_m"] < 5.0

    reading = {"proximity_distance_m": 10.0}
    apply_scenario(reading, "proximity_critical", rng_state._rng)
    assert reading["proximity_distance_m"] < 2.0


def test_unknown_scenario_rejected():
    assert not is_known_scenario("nonexistent_scenario")
    with pytest.raises(ValueError):
        apply_scenario({}, "nonexistent_scenario", None)


def test_seed_state_skips_maintenance_and_offline_machines():
    states = load_seed_state()
    machines = read_csv("machines.csv")
    off_ids = {int(m["id"]) for m in machines if m["status"] in ("maintenance", "offline")}
    assert not (set(states.keys()) & off_ids), "maintenance/offline machines must not stream"


def test_scenario_control_endpoint_contract():
    """Exercises POST /simulator/scenario per API_CONTRACT.md §3.3, in dry-run
    mode so no real backend or network call is needed."""
    from fastapi.testclient import TestClient

    app = create_app(backend_url="http://unused", interval_seconds=5, dry_run=True)
    with TestClient(app) as client:
        states = load_seed_state()
        any_machine_id = next(iter(states.keys()))

        resp = client.post("/simulator/scenario", json={
            "machine_id": any_machine_id, "scenario": "hydraulic_overheat", "duration_seconds": 30
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"status": "scenario_started", "machine_id": any_machine_id,
                         "scenario": "hydraulic_overheat"}

        resp = client.post("/simulator/scenario", json={
            "machine_id": any_machine_id, "scenario": "not_a_real_scenario", "duration_seconds": 30
        })
        assert resp.status_code == 422

        resp = client.post("/simulator/scenario", json={
            "machine_id": 999999, "scenario": "hydraulic_overheat", "duration_seconds": 30
        })
        assert resp.status_code == 404
