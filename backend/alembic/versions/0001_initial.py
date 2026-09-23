"""Initial CAT Operator Copilot schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "operators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False, unique=True),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("role", sa.String(20), nullable=False, server_default="operator"),
        sa.Column("experience_years", sa.Numeric(4,1)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine_code", sa.String(50), nullable=False, unique=True),
        sa.Column("machine_type", sa.String(50), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_machines_type", "machines", ["machine_type"])
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id"), nullable=False),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id"), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("site_zone", sa.String(80)),
        sa.Column("weather_condition", sa.String(30)),
        sa.Column("status", sa.String(20), nullable=False, server_default="assigned"),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer()),
        sa.Column("actual_duration_minutes", sa.Integer()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_tasks_operator_date", "tasks", ["operator_id", "scheduled_date"])
    op.create_index("idx_tasks_machine", "tasks", ["machine_id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_table(
        "machine_readings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("engine_temp_c", sa.Numeric(5,2)),
        sa.Column("hydraulic_pressure_psi", sa.Numeric(7,2)),
        sa.Column("fuel_level_pct", sa.Numeric(5,2)),
        sa.Column("rpm", sa.Integer()),
        sa.Column("idle_time_seconds", sa.Integer()),
        sa.Column("vibration_level", sa.Numeric(6,3)),
        sa.Column("load_weight_kg", sa.Numeric(8,2)),
        sa.Column("ambient_temp_c", sa.Numeric(5,2)),
        sa.Column("seatbelt_status", sa.Boolean()),
        sa.Column("proximity_distance_m", sa.Numeric(6,2)),
        sa.Column("safety_alert_triggered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("anomaly_score", sa.Numeric(6,4)),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("idx_readings_machine_time", "machine_readings", ["machine_id", "recorded_at"])
    op.create_index("idx_readings_task", "machine_readings", ["task_id"])
    op.create_index("idx_readings_anomaly", "machine_readings", ["is_anomaly"], postgresql_where=sa.text("is_anomaly = true"))
    op.create_index("idx_readings_safety_alert", "machine_readings", ["safety_alert_triggered"], postgresql_where=sa.text("safety_alert_triggered = true"))
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id"), nullable=False),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id")),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id")),
        sa.Column("reading_id", sa.BigInteger(), sa.ForeignKey("machine_readings.id")),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("explanation_text", sa.Text()),
        sa.Column("recommended_action", sa.Text()),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_alerts_machine_time", "alerts", ["machine_id", "detected_at"])
    op.create_index("idx_alerts_operator_status", "alerts", ["operator_id", "status"])
    op.create_index("idx_alerts_type", "alerts", ["alert_type"])
    op.create_table(
        "training_content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("related_alert_type", sa.String(50)),
        sa.Column("machine_type", sa.String(50)),
        sa.Column("media_url", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_training_alert_type", "training_content", ["related_alert_type"])
    op.create_table(
        "task_time_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("machine_type", sa.String(50), nullable=False),
        sa.Column("site_zone", sa.String(80)),
        sa.Column("weather_condition", sa.String(30)),
        sa.Column("operator_experience_years", sa.Numeric(4,1)),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_task_time_logs_type", "task_time_logs", ["task_type", "machine_type"])
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operators.id"), nullable=False),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id")),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_incidents_operator", "incidents", ["operator_id"])
    op.create_index("idx_incidents_machine", "incidents", ["machine_id"])

def downgrade():
    op.drop_index("idx_incidents_machine", table_name="incidents")
    op.drop_index("idx_incidents_operator", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("idx_task_time_logs_type", table_name="task_time_logs")
    op.drop_table("task_time_logs")
    op.drop_index("idx_training_alert_type", table_name="training_content")
    op.drop_table("training_content")
    op.drop_index("idx_alerts_type", table_name="alerts")
    op.drop_index("idx_alerts_operator_status", table_name="alerts")
    op.drop_index("idx_alerts_machine_time", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("idx_readings_safety_alert", table_name="machine_readings")
    op.drop_index("idx_readings_anomaly", table_name="machine_readings")
    op.drop_index("idx_readings_task", table_name="machine_readings")
    op.drop_index("idx_readings_machine_time", table_name="machine_readings")
    op.drop_table("machine_readings")
    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_index("idx_tasks_machine", table_name="tasks")
    op.drop_index("idx_tasks_operator_date", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("idx_machines_type", table_name="machines")
    op.drop_table("machines")
    op.drop_table("operators")
