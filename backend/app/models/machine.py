from sqlalchemy import Integer, String, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Machine(Base):
    __tablename__ = "machines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    machine_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (Index("idx_machines_type", "machine_type"),)

    tasks = relationship("Task", back_populates="machine")
    readings = relationship("MachineReading", back_populates="machine")
    alerts = relationship("Alert", back_populates="machine")
    incidents = relationship("Incident", back_populates="machine")
