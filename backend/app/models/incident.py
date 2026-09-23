from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), nullable=False)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), nullable=False)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        Index("idx_incidents_operator", "operator_id"),
        Index("idx_incidents_machine", "machine_id"),
    )
    operator = relationship("Operator", back_populates="incidents")
    machine = relationship("Machine", back_populates="incidents")
    alert = relationship("Alert", back_populates="incidents")
