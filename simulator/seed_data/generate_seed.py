"""
generate_seed.py — CAT Operator Copilot seed data generator (Member 3 scope only)

Generates deterministic, schema-exact seed data for:
  - operators           (DATABASE_DESIGN.md §1)
  - machines            (DATABASE_DESIGN.md §2)
  - tasks               (DATABASE_DESIGN.md §3)
  - task_time_logs      (DATABASE_DESIGN.md §7)

Outputs CSVs (for inspection / loading via any tool) and a single seed.sql
(ready for `psql <db> -f seed.sql`) with explicit ids + a sequence reset per
table so future SERIAL inserts don't collide with seeded rows.

Does NOT create machine_readings, alerts, incidents, or training_content —
those are either produced live by the simulator through POST /machine-events
(readings) or owned by Member 1/2 (alerts/incidents/training_content are
backend-generated or frontend-authored, per PROJECT_PLAN.md §7).

Deterministic: fixed RNG seed (42) — re-running this script produces byte-
identical output, which is the point (reproducible demo dataset).
"""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
OUT_DIR = Path(__file__).parent

# Locked vocab — must match DATABASE_DESIGN.md / API_CONTRACT.md exactly.
MACHINE_TYPES = ["excavator", "dozer", "loader", "grader"]
MACHINE_MODELS = {
    "excavator": ["CAT 320", "CAT 336", "CAT 315"],
    "dozer": ["CAT D6", "CAT D8T"],
    "loader": ["CAT 950", "CAT 966"],
    "grader": ["CAT 140"],
}
TASK_TYPES = ["trenching", "grading", "material_loading", "excavation", "dozing", "hauling"]
WEATHER_CONDITIONS = ["clear", "rain", "extreme_heat", "overcast", "wind"]
SITE_ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"]
LANGUAGES = ["en", "ta", "hi"]

TODAY = date(2026, 9, 23)  # matches current project date; keeps demo data "today"-relevant


def gen_operators(rng, n=8):
    first_names = ["Raj", "Ananya", "Suresh", "Priya", "Vikram", "Meena", "Arun", "Divya",
                   "Karthik", "Lakshmi"]
    last_names = ["Kumar", "Iyer", "Nair", "Reddy", "Menon", "Pillai", "Rao", "Krishnan"]
    rows = []
    for i in range(1, n + 1):
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        rows.append({
            "id": i,
            "name": name,
            "employee_code": f"OP-{1000 + i}",
            "preferred_language": rng.choices(LANGUAGES, weights=[5, 3, 2])[0],
            "role": "supervisor" if i == n else "operator",  # last operator doubles as supervisor
            "experience_years": round(rng.uniform(0.5, 18.0), 1),
        })
    return rows


def gen_machines(rng, n=6):
    rows = []
    statuses = ["active", "active", "active", "idle", "idle", "maintenance"]
    for i in range(1, n + 1):
        mtype = MACHINE_TYPES[(i - 1) % len(MACHINE_TYPES)]
        rows.append({
            "id": i,
            "machine_code": f"{mtype[:3].upper()}-{200 + i}",
            "machine_type": mtype,
            "model": rng.choice(MACHINE_MODELS[mtype]),
            "status": statuses[(i - 1) % len(statuses)],
        })
    return rows


def gen_tasks(rng, operators, machines, n=30):
    """
    Mix of statuses across a date window ending today, so the dashboard has:
      - a few 'in_progress' tasks TODAY (for the simulator to stream against)
      - a few 'assigned' tasks TODAY (not yet started)
      - a spread of 'completed' tasks over the past 2 weeks (feeds realism;
        actual task_time_logs history is generated separately/independently)
      - one 'cancelled' task for status-variety
    """
    rows = []
    operator_ids = [o["id"] for o in operators]
    machine_ids = [m["id"] for m in machines]

    task_id = 1
    # Today's tasks: guarantee at least 2 in_progress + 2 assigned for the demo.
    today_specs = [
        ("in_progress", machines[0]["id"]),
        ("in_progress", machines[2]["id"]),
        ("assigned", machines[1]["id"]),
        ("assigned", machines[3]["id"]),
    ]
    for status, machine_id in today_specs:
        op_id = rng.choice(operator_ids)
        task_type = rng.choice(TASK_TYPES)
        weather = rng.choice(WEATHER_CONDITIONS)
        zone = rng.choice(SITE_ZONES)
        est = rng.randint(45, 150)
        started_at = None
        completed_at = None
        actual = None
        if status == "in_progress":
            started_at = datetime.combine(TODAY, datetime.min.time()) + timedelta(
                hours=rng.randint(6, 9), minutes=rng.randint(0, 59)
            )
        rows.append({
            "id": task_id, "operator_id": op_id, "machine_id": machine_id,
            "task_type": task_type, "site_zone": zone, "weather_condition": weather,
            "status": status, "scheduled_date": TODAY.isoformat(),
            "estimated_duration_minutes": est, "actual_duration_minutes": actual,
            "started_at": started_at.isoformat() + "Z" if started_at else "",
            "completed_at": "",
        })
        task_id += 1

    # One cancelled task today, for status variety.
    rows.append({
        "id": task_id, "operator_id": rng.choice(operator_ids), "machine_id": rng.choice(machine_ids),
        "task_type": rng.choice(TASK_TYPES), "site_zone": rng.choice(SITE_ZONES),
        "weather_condition": rng.choice(WEATHER_CONDITIONS), "status": "cancelled",
        "scheduled_date": TODAY.isoformat(), "estimated_duration_minutes": rng.randint(45, 150),
        "actual_duration_minutes": None, "started_at": "", "completed_at": "",
    })
    task_id += 1

    # Past 14 days: completed tasks with actual_duration_minutes recorded.
    while task_id <= n:
        days_ago = rng.randint(1, 14)
        d = TODAY - timedelta(days=days_ago)
        est = rng.randint(45, 150)
        # actual duration realistically close to estimate, +/- variance, occasionally an outlier
        variance = rng.choice([0.85, 0.95, 1.0, 1.05, 1.15, 1.4])  # 1.4 = the occasional bad day
        actual = max(10, round(est * variance))
        start_dt = datetime.combine(d, datetime.min.time()) + timedelta(
            hours=rng.randint(6, 14), minutes=rng.randint(0, 59)
        )
        end_dt = start_dt + timedelta(minutes=actual)
        rows.append({
            "id": task_id, "operator_id": rng.choice(operator_ids), "machine_id": rng.choice(machine_ids),
            "task_type": rng.choice(TASK_TYPES), "site_zone": rng.choice(SITE_ZONES),
            "weather_condition": rng.choice(WEATHER_CONDITIONS), "status": "completed",
            "scheduled_date": d.isoformat(), "estimated_duration_minutes": est,
            "actual_duration_minutes": actual,
            "started_at": start_dt.isoformat() + "Z", "completed_at": end_dt.isoformat() + "Z",
        })
        task_id += 1

    return rows


def gen_task_time_logs(rng, n=150):
    """
    Independent historical training set for the task-time regression model
    (§6a input set: task_type, machine_type, site_zone, weather_condition,
    operator_experience_years, + duration_minutes label). Spans ~120 days so
    every (task_type, machine_type) pair used by the fallback chain has
    enough rows to average meaningfully.
    """
    rows = []
    # Base duration profile per (task_type, machine_type) so the "mean for matching pair"
    # fallback step actually means something distinct per pair, with realistic spread.
    base_minutes = {}
    for t in TASK_TYPES:
        for m in MACHINE_TYPES:
            base_minutes[(t, m)] = rng.randint(50, 140)

    weather_modifier = {"clear": 1.0, "overcast": 1.02, "wind": 1.05, "rain": 1.2, "extreme_heat": 1.15}

    for i in range(1, n + 1):
        task_type = rng.choice(TASK_TYPES)
        machine_type = rng.choice(MACHINE_TYPES)
        weather = rng.choices(
            WEATHER_CONDITIONS, weights=[45, 15, 10, 20, 10]
        )[0]
        zone = rng.choice(SITE_ZONES)
        exp_years = round(rng.uniform(0.5, 18.0), 1)
        base = base_minutes[(task_type, machine_type)]
        # More experience -> modestly faster; bad weather -> slower; plus noise.
        exp_factor = 1.0 - min(exp_years, 15) * 0.012  # up to ~18% faster at 15+ yrs
        noise = rng.gauss(1.0, 0.08)
        duration = max(15, round(base * exp_factor * weather_modifier[weather] * noise))
        days_ago = rng.randint(1, 120)
        rows.append({
            "id": i,
            "task_type": task_type,
            "machine_type": machine_type,
            "site_zone": zone,
            "weather_condition": weather,
            "operator_experience_years": exp_years,
            "duration_minutes": duration,
            "recorded_date": (TODAY - timedelta(days=days_ago)).isoformat(),
        })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def sql_str(v):
    if v is None or v == "":
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def write_sql(path, operators, machines, tasks, task_time_logs):
    lines = [
        "-- seed.sql — CAT Operator Copilot seed data",
        "-- Generated by simulator/seed_data/generate_seed.py (seed=42, deterministic).",
        "-- Matches DATABASE_DESIGN.md exactly. Safe to re-run against an empty schema.",
        "BEGIN;",
        "",
        "-- 1. operators",
    ]
    for o in operators:
        lines.append(
            "INSERT INTO operators (id, name, employee_code, preferred_language, role, experience_years) "
            f"VALUES ({o['id']}, {sql_str(o['name'])}, {sql_str(o['employee_code'])}, "
            f"{sql_str(o['preferred_language'])}, {sql_str(o['role'])}, {o['experience_years']});"
        )
    lines.append("SELECT setval('operators_id_seq', (SELECT MAX(id) FROM operators));")
    lines.append("")
    lines.append("-- 2. machines")
    for m in machines:
        lines.append(
            "INSERT INTO machines (id, machine_code, machine_type, model, status) "
            f"VALUES ({m['id']}, {sql_str(m['machine_code'])}, {sql_str(m['machine_type'])}, "
            f"{sql_str(m['model'])}, {sql_str(m['status'])});"
        )
    lines.append("SELECT setval('machines_id_seq', (SELECT MAX(id) FROM machines));")
    lines.append("")
    lines.append("-- 3. tasks")
    for t in tasks:
        lines.append(
            "INSERT INTO tasks (id, operator_id, machine_id, task_type, site_zone, weather_condition, "
            "status, scheduled_date, estimated_duration_minutes, actual_duration_minutes, started_at, completed_at) "
            f"VALUES ({t['id']}, {t['operator_id']}, {t['machine_id']}, {sql_str(t['task_type'])}, "
            f"{sql_str(t['site_zone'])}, {sql_str(t['weather_condition'])}, {sql_str(t['status'])}, "
            f"{sql_str(t['scheduled_date'])}, {sql_str(t['estimated_duration_minutes'])}, "
            f"{sql_str(t['actual_duration_minutes'])}, {sql_str(t['started_at'])}, {sql_str(t['completed_at'])});"
        )
    lines.append("SELECT setval('tasks_id_seq', (SELECT MAX(id) FROM tasks));")
    lines.append("")
    lines.append("-- 4. task_time_logs")
    for r in task_time_logs:
        lines.append(
            "INSERT INTO task_time_logs (id, task_type, machine_type, site_zone, weather_condition, "
            "operator_experience_years, duration_minutes, recorded_date) "
            f"VALUES ({r['id']}, {sql_str(r['task_type'])}, {sql_str(r['machine_type'])}, "
            f"{sql_str(r['site_zone'])}, {sql_str(r['weather_condition'])}, {r['operator_experience_years']}, "
            f"{r['duration_minutes']}, {sql_str(r['recorded_date'])});"
        )
    lines.append("SELECT setval('task_time_logs_id_seq', (SELECT MAX(id) FROM task_time_logs));")
    lines.append("")
    lines.append("COMMIT;")
    path.write_text("\n".join(lines) + "\n")


def main():
    rng = random.Random(SEED)
    operators = gen_operators(rng)
    machines = gen_machines(rng)
    tasks = gen_tasks(rng, operators, machines)
    task_time_logs = gen_task_time_logs(rng)

    write_csv(OUT_DIR / "operators.csv", operators,
              ["id", "name", "employee_code", "preferred_language", "role", "experience_years"])
    write_csv(OUT_DIR / "machines.csv", machines,
              ["id", "machine_code", "machine_type", "model", "status"])
    write_csv(OUT_DIR / "tasks.csv", tasks,
              ["id", "operator_id", "machine_id", "task_type", "site_zone", "weather_condition",
               "status", "scheduled_date", "estimated_duration_minutes", "actual_duration_minutes",
               "started_at", "completed_at"])
    write_csv(OUT_DIR / "task_time_logs.csv", task_time_logs,
              ["id", "task_type", "machine_type", "site_zone", "weather_condition",
               "operator_experience_years", "duration_minutes", "recorded_date"])
    write_sql(OUT_DIR / "seed.sql", operators, machines, tasks, task_time_logs)

    print(f"operators: {len(operators)} rows")
    print(f"machines: {len(machines)} rows")
    print(f"tasks: {len(tasks)} rows "
          f"(in_progress={sum(1 for t in tasks if t['status']=='in_progress')}, "
          f"assigned={sum(1 for t in tasks if t['status']=='assigned')}, "
          f"completed={sum(1 for t in tasks if t['status']=='completed')}, "
          f"cancelled={sum(1 for t in tasks if t['status']=='cancelled')})")
    print(f"task_time_logs: {len(task_time_logs)} rows")


if __name__ == "__main__":
    main()
