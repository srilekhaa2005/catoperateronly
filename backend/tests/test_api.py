from datetime import date, datetime, timezone
from app.models import Operator, Machine, Task, TaskTimeLog

def seed_basic(db):
    op=Operator(name="Test Operator",employee_code="API-1",preferred_language="en",experience_years=5)
    m=Machine(machine_code="API-EXC-1",machine_type="excavator",model="CAT 320")
    db.add_all([op,m]); db.flush()
    t=Task(operator_id=op.id,machine_id=m.id,task_type="trenching",site_zone="Zone A",weather_condition="clear",scheduled_date=date.today(),status="assigned")
    db.add(t)
    for i in range(10):
        db.add(TaskTimeLog(task_type="trenching",machine_type="excavator",site_zone="Zone A",weather_condition="clear",operator_experience_years=5,duration_minutes=90+i,recorded_date=date.today()))
    db.commit(); return op,m,t

def test_core_routes(client, db):
    op,m,t=seed_basic(db)
    assert client.get(f"/api/operators/{op.id}").status_code==200
    assert client.get(f"/api/operators/{op.id}/tasks?date={date.today().isoformat()}").status_code==200
    assert client.get(f"/api/tasks/{t.id}/estimate").status_code==200
    payload={"machine_id":m.id,"task_id":t.id,"recorded_at":datetime.now(timezone.utc).isoformat(),"engine_temp_c":118,"hydraulic_pressure_psi":3100,"fuel_level_pct":60,"rpm":1800,"idle_time_seconds":0,"vibration_level":1.1,"load_weight_kg":3000,"ambient_temp_c":34,"seatbelt_status":False,"proximity_distance_m":1.2,"is_simulated":True}
    r=client.post("/api/machine-events",json=payload)
    assert r.status_code==201
    assert r.json()["alerts_created"]>=2
    alerts=client.get(f"/api/operators/{op.id}/alerts").json()["alerts"]
    assert len(alerts)>=2
    alert_id=alerts[0]["id"]
    assert client.get(f"/api/alerts/{alert_id}").status_code==200
    assert client.get(f"/api/alerts/{alert_id}/explain?lang=ta").status_code==200
    assert client.get("/api/training-content?lang=en").status_code==200
