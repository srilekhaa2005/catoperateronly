from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), nullable=False)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    site_zone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weather_condition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="assigned")
    scheduled_date: Mapped[object] = mapped_column(Date, nullable=False)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_tasks_operator_date", "operator_id", "scheduled_date"),
        Index("idx_tasks_machine", "machine_id"),
        Index("idx_tasks_status", "status"),
    )
    operator = relationship("Operator", back_populates="tasks")
    machine = relationship("Machine", back_populates="tasks")
    readings = relationship("MachineReading", back_populates="task")
    alerts = relationship("Alert", back_populates="task")
