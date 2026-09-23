from sqlalchemy import Integer, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

class Operator(Base):
    __tablename__ = "operators"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="operator")
    experience_years: Mapped[float | None] = mapped_column(Numeric(4,1), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    tasks = relationship("Task", back_populates="operator")
    alerts = relationship("Alert", back_populates="operator")
    incidents = relationship("Incident", back_populates="operator")
