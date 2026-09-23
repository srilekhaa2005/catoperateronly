from sqlalchemy import Date, DateTime, Integer, Numeric, String, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class TaskTimeLog(Base):
    __tablename__ = "task_time_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    site_zone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weather_condition: Mapped[str | None] = mapped_column(String(30), nullable=True)
    operator_experience_years: Mapped[float | None] = mapped_column(Numeric(4,1), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_date: Mapped[object] = mapped_column(Date, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (Index("idx_task_time_logs_type", "task_type", "machine_type"),)
