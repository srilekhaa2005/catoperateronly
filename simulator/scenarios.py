"""
scenarios.py — named abnormal telemetry scenarios.

Each scenario is a pure function: (reading dict, rng) -> mutated reading dict.
Scenarios only change field VALUES on a reading that MachineState already
built; they never touch the database and never decide whether an alert
fires — that's the backend's rule/ML layer (API_CONTRACT.md §3.1,
DATABASE_DESIGN.md `machine_readings` locked thresholds). This module's job
is purely to make the abnormal condition "physically" present in the
simulated sensor values, the same way a real fault would.

Scenario names match the alert_type vocabulary in DATABASE_DESIGN.md's
`alerts.alert_type` column, plus "hydraulic_overheat" for the exact example
given in API_CONTRACT.md §3.3. "normal" resets a machine early if needed
(not itself an abnormal scenario).
"""

SCENARIO_NAMES = [
    "normal",
    "hydraulic_overheat",
    "excessive_idle",
    "low_hydraulic_pressure",
    "high_fuel_consumption",
    "unusual_vibration",
    "seatbelt_unfastened",
    "proximity_warning",
    "proximity_critical",
]


def is_known_scenario(name: str) -> bool:
    return name in SCENARIO_NAMES


def apply_scenario(reading: dict, scenario: str, rng) -> dict:
    """Mutate `reading` in place to reflect `scenario`; returns it for convenience."""
    if scenario == "normal":
        return reading

    if scenario == "hydraulic_overheat":
        reading["engine_temp_c"] = round(rng.uniform(110.0, 126.0), 1)
        reading["hydraulic_pressure_psi"] = round(rng.uniform(2900.0, 3350.0), 1)

    elif scenario == "excessive_idle":
        # idle_time_seconds is driven by MachineState (active=False during this
        # scenario); here we just ensure it reads clearly past the "excessive"
        # threshold used in the project brief (> ~30 min) and RPM looks idle-low.
        reading["idle_time_seconds"] = max(reading.get("idle_time_seconds", 0), 1800)
        reading["rpm"] = rng.randint(600, 750)
        reading["load_weight_kg"] = 0.0

    elif scenario == "low_hydraulic_pressure":
        reading["hydraulic_pressure_psi"] = round(rng.uniform(850.0, 1400.0), 1)

    elif scenario == "high_fuel_consumption":
        # "Low load cycles + high fuel consumption" per project brief: load stays
        # low while fuel drains much faster than the normal burn rate.
        reading["load_weight_kg"] = round(rng.uniform(0.0, 400.0), 1)
        reading["fuel_level_pct"] = max(1.0, round(reading["fuel_level_pct"] - rng.uniform(3.0, 6.0), 2))

    elif scenario == "unusual_vibration":
        reading["vibration_level"] = round(rng.uniform(4.0, 6.5), 2)

    elif scenario == "seatbelt_unfastened":
        reading["seatbelt_status"] = False

    elif scenario == "proximity_warning":
        reading["proximity_distance_m"] = round(rng.uniform(2.0, 4.9), 1)

    elif scenario == "proximity_critical":
        reading["proximity_distance_m"] = round(rng.uniform(0.2, 1.9), 1)

    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    return reading
