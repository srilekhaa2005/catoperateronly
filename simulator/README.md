# Machine Data Simulator — Data + Simulation (Member 3 scope)

Owns: seed dataset + machine telemetry simulator, per `PROJECT_PLAN.md` §7 and
`README.md`'s project structure. Does **not** include backend detection
logic, ML models, database schema/migrations, or frontend — those are Member
1 / Member 2's code.

## Contents

```
simulator/
├── seed_data/
│   ├── generate_seed.py     # deterministic generator (seed=42) for all 4 CSVs + seed.sql
│   ├── operators.csv        # 8 operators, incl. experience_years
│   ├── machines.csv         # 6 machines across all 4 machine_types
│   ├── tasks.csv            # 30 tasks: 2 in_progress, 2 assigned, 1 cancelled, 25 completed (past 14 days)
│   ├── task_time_logs.csv   # 150 rows of historical duration data for the regression model
│   └── seed.sql             # ready-to-run `psql <db> -f seed.sql` (explicit ids + sequence resets)
├── machine_state.py         # per-machine telemetry "physics" (drift, fuel burn, idle accumulation)
├── scenarios.py             # named abnormal scenarios (pure functions over a reading dict)
├── simulate.py              # main process: emitter loop + POST /simulator/scenario control API
├── tests/test_validation.py # seed-data + simulator-output validation (pytest)
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd simulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Seed CSVs and `seed.sql` are already generated and checked in. To regenerate
(byte-identical, since the RNG seed is fixed):

```bash
python seed_data/generate_seed.py
```

Load into Postgres once Member 1's schema exists:

```bash
psql cat_operator_copilot -f seed_data/seed.sql
```

## Running the simulator

```bash
python simulate.py --interval 5
```

This starts one process that:
- every 5s, generates a reading for every machine that isn't `maintenance`/
  `offline`, and POSTs it to `{BACKEND_URL}/machine-events` (the only
  ingestion path — see `API_CONTRACT.md` §3.1)
- serves `POST /simulator/scenario` on port 8100 (configurable via
  `--port` / `SIMULATOR_PORT`) so a presenter can trigger an abnormal
  scenario live during the demo

**No backend yet?** Run with `--dry-run` — readings print to stdout instead
of being POSTed, so you can develop/demo the simulator in isolation:

```bash
python simulate.py --interval 5 --dry-run
```

### Triggering a scenario during a demo

```bash
curl -X POST http://localhost:8100/simulator/scenario \
  -H "Content-Type: application/json" \
  -d '{"machine_id": 1, "scenario": "hydraulic_overheat", "duration_seconds": 60}'
```

`GET http://localhost:8100/simulator/status` shows what every machine is
currently doing (debug-only; not part of `API_CONTRACT.md`).

## Scenarios available

| Scenario name | What it does | Maps toward (backend's decision, not the simulator's) |
|---|---|---|
| `normal` | Resets a machine to baseline early | n/a |
| `hydraulic_overheat` | Engine temp → 110–126°C, hydraulic pressure → 2900–3350 psi | `overheat` alert |
| `excessive_idle` | Machine goes idle, `idle_time_seconds` forced ≥ 1800s, load → 0 | `excessive_idle` alert |
| `low_hydraulic_pressure` | Hydraulic pressure → 850–1400 psi | `low_hydraulic_pressure` alert |
| `high_fuel_consumption` | Low load + fast fuel drain ("low load cycles + high fuel consumption" per project brief) | anomaly (Isolation Forest) |
| `unusual_vibration` | Vibration → 4.0–6.5 (baseline ~0.6–1.6) | `unusual_vibration` alert |
| `seatbelt_unfastened` | `seatbelt_status = false` | `seatbelt_unfastened`, locked `critical` per §6b |
| `proximity_warning` | `proximity_distance_m` → 2.0–4.9 | `proximity_breach`, locked `warning` per §6b |
| `proximity_critical` | `proximity_distance_m` → 0.2–1.9 | `proximity_breach`, locked `critical` per §6b |

Scenario values are picked to sit clearly on the correct side of the locked
safety thresholds in `DATABASE_DESIGN.md` (`machine_readings` notes) and
`API_CONTRACT.md` §3.1 — the simulator makes the abnormal *sensor values*
appear; the backend's rule/ML layer decides whether an alert fires.

## Reproducibility

Every `MachineState` is seeded from `SIM_SEED + machine_id` (default
`SIM_SEED=42`). Re-running the simulator with the same seed and the same
sequence of scenario triggers reproduces the identical reading stream —
useful for rehearsing a demo so it behaves the same way every time.

## Validation

```bash
pytest tests/ -v
```

19 checks covering: seed CSV shape/FK integrity/enum validity, every
`(task_type, machine_type)` pair used in `tasks.csv` having historical
coverage in `task_time_logs.csv` (so the §6a fallback chain never has to
fall back to the global mean unnecessarily), reading payload shape against
`API_CONTRACT.md` §3.1, determinism given a fixed seed, every declared
scenario applying without error, each safety-critical scenario landing on
the correct side of the locked thresholds, and the `/simulator/scenario`
control endpoint's 200/422/404 behavior.

## Backend integration assumptions

These are the assumptions this simulator makes about the (not-yet-built)
backend, since it was built in parallel against the frozen contracts:

1. `POST /machine-events` accepts the exact field set in `API_CONTRACT.md`
   §3.1 and returns `201` on success; the simulator logs (but does not
   retry) failed POSTs, since a hackathon demo favors visibility over
   resilience.
2. `machine_id`/`task_id` values in seed data (1–6 for machines, matching
   `tasks.csv` for tasks) are the same ids the backend will have after
   loading `seed.sql` — i.e., the backend loads this seed data as-is rather
   than generating its own.
3. `POST /simulator/scenario` is hosted **by this simulator process**, not
   the backend — confirmed by `PROJECT_PLAN.md` §6's architecture diagram,
   which draws that endpoint's arrow into the "Machine Data Simulator" box.
   The backend never receives scenario-control requests directly.
4. Machines with seed `status = 'maintenance'` or `'offline'` never stream —
   the backend shouldn't expect readings for those `machine_id`s during a
   run.
