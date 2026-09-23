"""
simulate.py — Machine Data Simulator (Member 3 scope).

Run:
    python simulate.py --interval 5

What it does:
  1. Loads seed machines/tasks (seed_data/machines.csv, tasks.csv) to know which
     machines are "on" and which have an in_progress task right now.
  2. Every `--interval` seconds, generates one reading per active machine and
     sends it via POST {BACKEND_URL}/machine-events — the ONLY path readings
     enter the system (API_CONTRACT.md §3.1, PROJECT_PLAN.md §6). This script
     never writes to PostgreSQL directly.
  3. Hosts POST /simulator/scenario (API_CONTRACT.md §3.3) — a demo-control-only
     endpoint that tells this process to start emitting a named abnormal
     scenario for a machine. It never touches the database; it only flips this
     process's internal state so the *next* readings sent through
     POST /machine-events look abnormal.

Both the background emitter loop and the scenario control API run in the same
process (single `python simulate.py` command, matching README.md's run
instructions), using FastAPI + an asyncio background task.

Use --dry-run to print generated readings instead of POSTing them anywhere —
useful for local testing before a backend exists (see tests/test_validation.py).
"""

import argparse
import asyncio
import csv
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from machine_state import MachineState
from scenarios import is_known_scenario

SEED_DIR = Path(__file__).parent / "seed_data"
DEFAULT_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api")
SIM_SEED = int(os.environ.get("SIM_SEED", "42"))

# Populated at startup by load_seed_state(); keyed by machine_id.
machine_states: dict[int, MachineState] = {}

# Simple in-memory log of every reading sent this run — used by tests and by
# the optional /simulator/status debug endpoint. Not part of the API contract.
sent_readings_log: list[dict] = []


def load_seed_state(sim_seed: int = SIM_SEED) -> dict[int, MachineState]:
    """Build initial MachineState per machine from seed CSVs.

    Machines with status 'maintenance' or 'offline' are skipped entirely —
    a machine that's off doesn't stream telemetry. Machines with an
    'in_progress' task today stream as active with that task's task_id and
    weather_condition; other 'idle'/'active' machines stream idle readings
    with task_id=None (per DATABASE_DESIGN.md machine_readings.task_id note:
    nullable for readings from a machine with no active task).
    """
    machines_path = SEED_DIR / "machines.csv"
    tasks_path = SEED_DIR / "tasks.csv"
    if not machines_path.exists() or not tasks_path.exists():
        raise FileNotFoundError(
            "Seed data not found — run `python seed_data/generate_seed.py` first."
        )

    machines = {}
    with open(machines_path) as f:
        for row in csv.DictReader(f):
            machines[int(row["id"])] = row

    active_task_by_machine = {}
    with open(tasks_path) as f:
        for row in csv.DictReader(f):
            if row["status"] == "in_progress":
                active_task_by_machine[int(row["machine_id"])] = row

    states = {}
    for machine_id, m in machines.items():
        if m["status"] in ("maintenance", "offline"):
            continue
        task = active_task_by_machine.get(machine_id)
        states[machine_id] = MachineState(
            machine_id=machine_id,
            machine_type=m["machine_type"],
            task_id=int(task["id"]) if task else None,
            weather_condition=task["weather_condition"] if task else "clear",
            is_task_active=bool(task),
            sim_seed=sim_seed,
        )
    return states


async def send_reading(client: Optional[httpx.AsyncClient], backend_url: str,
                        reading: dict, dry_run: bool) -> None:
    sent_readings_log.append(reading)
    if dry_run or client is None:
        print(f"[dry-run] machine {reading['machine_id']}: "
              f"engine_temp={reading['engine_temp_c']}C  "
              f"seatbelt={reading['seatbelt_status']}  "
              f"proximity={reading['proximity_distance_m']}m  "
              f"fuel={reading['fuel_level_pct']}%")
        return
    try:
        resp = await client.post(f"{backend_url}/machine-events", json=reading, timeout=5.0)
        if resp.status_code != 201:
            print(f"[warn] POST /machine-events -> {resp.status_code}: {resp.text[:200]}")
    except httpx.HTTPError as e:
        print(f"[warn] POST /machine-events failed: {e}")


async def emitter_loop(backend_url: str, interval_seconds: int, dry_run: bool,
                        stop_event: asyncio.Event):
    client = None if dry_run else httpx.AsyncClient()
    try:
        while not stop_event.is_set():
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            for state in machine_states.values():
                reading = state.next_reading(now_iso)
                await send_reading(client, backend_url, reading, dry_run)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                pass
    finally:
        if client is not None:
            await client.aclose()


# ---------------------------------------------------------------------------
# FastAPI app: POST /simulator/scenario (demo-control only — never touches DB)
# ---------------------------------------------------------------------------

class ScenarioRequest(BaseModel):
    machine_id: int
    scenario: str
    duration_seconds: int = 60


def create_app(backend_url: str, interval_seconds: int, dry_run: bool) -> FastAPI:
    stop_event = asyncio.Event()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global machine_states
        machine_states = load_seed_state()
        app.state.emitter_task = asyncio.create_task(
            emitter_loop(backend_url, interval_seconds, dry_run, stop_event)
        )
        print(f"Simulator started. backend={backend_url} interval={interval_seconds}s "
              f"dry_run={dry_run} machines={list(machine_states.keys())}")
        yield
        stop_event.set()
        await app.state.emitter_task

    app = FastAPI(title="CAT Operator Copilot — Machine Data Simulator", lifespan=lifespan)

    @app.post("/simulator/scenario", status_code=200)
    async def start_scenario(req: ScenarioRequest):
        if not is_known_scenario(req.scenario):
            raise HTTPException(status_code=422, detail=f"Unknown scenario: {req.scenario}")
        state = machine_states.get(req.machine_id)
        if state is None:
            raise HTTPException(
                status_code=404,
                detail=f"machine_id {req.machine_id} is not currently streaming "
                       "(unknown, or status is maintenance/offline)"
            )
        state.start_scenario(req.scenario, req.duration_seconds, interval_seconds)
        return {"status": "scenario_started", "machine_id": req.machine_id, "scenario": req.scenario}

    @app.get("/simulator/status")
    async def status():
        """Debug-only endpoint, not part of API_CONTRACT.md — quick visibility
        into what each machine is doing right now during a demo rehearsal."""
        return {
            mid: {
                "machine_type": s.machine_type,
                "task_id": s.task_id,
                "scenario": s.scenario,
                "fuel_level_pct": s.fuel_level_pct,
            }
            for mid, s in machine_states.items()
        }

    return app


def main():
    parser = argparse.ArgumentParser(description="CAT Operator Copilot machine data simulator")
    parser.add_argument("--interval", type=int, default=5, help="seconds between reading batches")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL,
                         help="base URL of the backend API (default: %(default)s)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("SIMULATOR_PORT", 8100)),
                         help="port to serve POST /simulator/scenario on")
    parser.add_argument("--dry-run", action="store_true",
                         help="print readings instead of POSTing them (no backend required)")
    args = parser.parse_args()

    import uvicorn
    app = create_app(args.backend_url, args.interval, args.dry_run)
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
