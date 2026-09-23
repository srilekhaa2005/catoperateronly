"""
machine_state.py — per-machine telemetry state.

Owns the "physics" of one simulated machine tick-to-tick: realistic baseline
values that drift with small noise, plus enough internal state (fuel level,
idle accumulator) to make the readings coherent over time rather than pure
random noise per tick.

Deterministic per machine: each MachineState is seeded from
`SIM_SEED + machine_id`, so a given (seed, machine_id, tick count) always
reproduces the same reading sequence — required for a repeatable demo.

This module has no knowledge of the API contract's field names beyond what
POST /machine-events documents (API_CONTRACT.md §3.1); it only produces
values, never decides safety/anomaly outcomes (that's the backend's job).
"""

import random
from dataclasses import dataclass, field

from scenarios import apply_scenario

# Baseline "normal operation" ranges, loosely realistic for mid-size CAT
# construction equipment. Not sourced from real telemetry — illustrative for
# a hackathon simulation, not a spec.
NORMAL_RANGES = {
    "engine_temp_c": (82.0, 96.0),
    "hydraulic_pressure_psi": (2100.0, 2600.0),
    "rpm_active": (1400, 2100),
    "rpm_idle": (650, 850),
    "vibration_level": (0.6, 1.6),
    "load_weight_kg_active": (1500.0, 4200.0),
}

WEATHER_AMBIENT_C = {
    "clear": (26.0, 34.0),
    "overcast": (23.0, 29.0),
    "wind": (22.0, 30.0),
    "rain": (20.0, 26.0),
    "extreme_heat": (38.0, 46.0),
}


@dataclass
class MachineState:
    machine_id: int
    machine_type: str
    task_id: int | None = None
    weather_condition: str = "clear"
    is_task_active: bool = True  # False -> machine idling with no assigned task

    fuel_level_pct: float = field(default=78.0)
    idle_time_seconds: int = 0
    sim_seed: int = 42
    _rng: random.Random = field(default=None, repr=False)

    # Scenario override state
    scenario: str = "normal"
    scenario_ticks_remaining: int = 0

    def __post_init__(self):
        self._rng = random.Random(self.sim_seed + self.machine_id)
        self.fuel_level_pct = round(self._rng.uniform(55.0, 95.0), 1)

    def start_scenario(self, scenario_name: str, duration_seconds: int, interval_seconds: int):
        self.scenario = scenario_name
        self.scenario_ticks_remaining = max(1, duration_seconds // max(1, interval_seconds))

    def _tick_scenario(self):
        if self.scenario != "normal":
            self.scenario_ticks_remaining -= 1
            if self.scenario_ticks_remaining <= 0:
                self.scenario = "normal"

    def next_reading(self, recorded_at_iso: str) -> dict:
        """Produce one reading dict, contract-shaped for POST /machine-events."""
        rng = self._rng
        r = NORMAL_RANGES

        active = self.is_task_active and self.scenario != "excessive_idle"
        rpm_lo, rpm_hi = r["rpm_active"] if active else r["rpm_idle"]

        if active:
            self.idle_time_seconds = 0
        else:
            self.idle_time_seconds += rng.randint(4, 6)

        ambient_lo, ambient_hi = WEATHER_AMBIENT_C.get(self.weather_condition, (25.0, 33.0))

        reading = {
            "machine_id": self.machine_id,
            "task_id": self.task_id,
            "recorded_at": recorded_at_iso,
            "engine_temp_c": round(rng.uniform(*r["engine_temp_c"]), 1),
            "hydraulic_pressure_psi": round(rng.uniform(*r["hydraulic_pressure_psi"]), 1),
            "fuel_level_pct": None,  # filled below
            "rpm": rng.randint(rpm_lo, rpm_hi),
            "idle_time_seconds": self.idle_time_seconds,
            "vibration_level": round(rng.uniform(*r["vibration_level"]), 2),
            "load_weight_kg": round(rng.uniform(*r["load_weight_kg_active"]), 1) if active else 0.0,
            "ambient_temp_c": round(rng.uniform(ambient_lo, ambient_hi), 1),
            "seatbelt_status": True,
            "proximity_distance_m": round(rng.uniform(6.0, 25.0), 1),
            "is_simulated": True,
        }

        # Normal fuel burn: faster while active.
        burn = rng.uniform(0.03, 0.09) if active else rng.uniform(0.005, 0.02)
        self.fuel_level_pct = max(3.0, round(self.fuel_level_pct - burn, 2))
        reading["fuel_level_pct"] = self.fuel_level_pct

        if self.scenario != "normal":
            apply_scenario(reading, self.scenario, rng)

        self._tick_scenario()
        return reading
