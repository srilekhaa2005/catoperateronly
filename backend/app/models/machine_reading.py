from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class MachineReading(Base):
    __tablename__ = "machine_readings"
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    recorded_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    engine_temp_c: Mapped[float | None] = mapped_column(Numeric(5,2))
    hydraulic_pressure_psi: Mapped[float | None] = mapped_column(Numeric(7,2))
    fuel_level_pct: Mapped[float | None] = mapped_column(Numeric(5,2))
    rpm: Mapped[int | None] = mapped_column(Integer)
    idle_time_seconds: Mapped[int | None] = mapped_column(Integer)
    vibration_level: Mapped[float | None] = mapped_column(Numeric(6,3))
    load_weight_kg: Mapped[float | None] = mapped_column(Numeric(8,2))
    ambient_temp_c: Mapped[float | None] = mapped_column(Numeric(5,2))
    seatbelt_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    proximity_distance_m: Mapped[float | None] = mapped_column(Numeric(6,2), nullable=True)
    safety_alert_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    anomaly_score: Mapped[float | None] = mapped_column(Numeric(6,4), nullable=True)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_readings_machine_time", "machine_id", "recorded_at"),
        Index("idx_readings_task", "task_id"),
        Index("idx_readings_anomaly", "is_anomaly", postgresql_where=(is_anomaly == True)),
        Index("idx_readings_safety_alert", "safety_alert_triggered", postgresql_where=(safety_alert_triggered == True)),
    )
    machine = relationship("Machine", back_populates="readings")
    task = relationship("Task", back_populates="readings")
    alerts = relationship("Alert", back_populates="reading")
