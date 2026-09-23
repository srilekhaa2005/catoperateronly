from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("operators.id"), nullable=True)
    reading_id: Mapped[int | None] = mapped_column(ForeignKey("machine_readings.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    acknowledged_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_alerts_machine_time", "machine_id", "detected_at"),
        Index("idx_alerts_operator_status", "operator_id", "status"),
        Index("idx_alerts_type", "alert_type"),
    )
    machine = relationship("Machine", back_populates="alerts")
    task = relationship("Task", back_populates="alerts")
    operator = relationship("Operator", back_populates="alerts")
    reading = relationship("MachineReading", back_populates="alerts")
    incidents = relationship("Incident", back_populates="alert")
