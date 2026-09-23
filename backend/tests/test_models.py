from datetime import date
from app.models import Operator, Machine, Task, TaskTimeLog, TrainingContent, Incident, Alert, MachineReading

def test_all_models_create(db):
    operator = Operator(name="Test Operator", employee_code="T-1")
    machine = Machine(machine_code="EXC-1", machine_type="excavator", model="CAT 320")
    db.add_all([operator, machine]); db.flush()
    task = Task(operator_id=operator.id, machine_id=machine.id, task_type="trenching",
                scheduled_date=date(2026, 9, 23), site_zone="Zone A", weather_condition="clear")
    db.add(task); db.flush()
    reading = MachineReading(machine_id=machine.id, task_id=task.id, engine_temp_c=90)
    db.add(reading); db.flush()
    alert = Alert(machine_id=machine.id, task_id=task.id, operator_id=operator.id, reading_id=reading.id,
                  alert_type="overheat", severity="critical")
    db.add(alert); db.flush()
    incident = Incident(operator_id=operator.id, machine_id=machine.id, alert_id=alert.id,
                        description="test", severity="warning")
    db.add(incident)
    db.add(TaskTimeLog(task_type="trenching", machine_type="excavator", duration_minutes=90, recorded_date=date(2026,9,1)))
    db.add(TrainingContent(title="Safety", body_text="Stay safe.", related_alert_type="overheat"))
    db.commit()
    assert operator.id and machine.id and task.id and reading.id and alert.id and incident.id

def test_nullable_reading_task(db):
    from app.models import Machine
    machine = Machine(machine_code="EXC-2", machine_type="excavator", model="CAT 320")
    db.add(machine); db.flush()
    reading = MachineReading(machine_id=machine.id)
    db.add(reading); db.commit()
    assert reading.task_id is None
