from dataclasses import dataclass

@dataclass(frozen=True)
class SafetyAlert:
    alert_type: str
    severity: str
    explanation: str
    action: str


def evaluate_safety(data: dict) -> list[SafetyAlert]:
    alerts: list[SafetyAlert] = []
    if data.get("seatbelt_status") is False:
        alerts.append(SafetyAlert(
            "seatbelt_unfastened", "critical",
            "The operator seatbelt is unfastened while the machine is operating.",
            "Stop the machine safely and fasten the seatbelt before continuing.",
        ))
    proximity = data.get("proximity_distance_m")
    if proximity is not None:
        if proximity < 2:
            alerts.append(SafetyAlert(
                "proximity_critical", "critical",
                "A person or obstacle is within the critical proximity zone.",
                "Stop the machine immediately and verify the area is clear.",
            ))
        elif proximity < 5:
            alerts.append(SafetyAlert(
                "proximity_warning", "warning",
                "A person or obstacle is inside the warning proximity zone.",
                "Reduce movement and verify the surrounding area before continuing.",
            ))
    temp = data.get("engine_temp_c")
    pressure = data.get("hydraulic_pressure_psi")
    if temp is not None and temp >= 110:
        alerts.append(SafetyAlert(
            "hydraulic_overheat", "critical",
            "Engine temperature is above the configured safe operating threshold.",
            "Stop the machine safely and inspect the hydraulic and cooling systems.",
        ))
    if pressure is not None and pressure < 1500:
        alerts.append(SafetyAlert(
            "low_hydraulic_pressure", "warning",
            "Hydraulic pressure is below the configured operating range.",
            "Pause operation and inspect the hydraulic system before continuing.",
        ))
    idle = data.get("idle_time_seconds")
    if idle is not None and idle >= 1800:
        alerts.append(SafetyAlert(
            "excessive_idle", "warning",
            "The machine has been idling for an extended period.",
            "Stop or resume productive work to reduce unnecessary idling and fuel use.",
        ))
    vibration = data.get("vibration_level")
    if vibration is not None and vibration >= 4:
        alerts.append(SafetyAlert(
            "unusual_vibration", "warning",
            "Machine vibration is above the configured normal range.",
            "Pause operation and inspect the machine for abnormal vibration sources.",
        ))
    return alerts
