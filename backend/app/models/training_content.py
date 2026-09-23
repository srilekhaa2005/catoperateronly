from sqlalchemy import DateTime, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

class TrainingContent(Base):
    __tablename__ = "training_content"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    related_alert_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    machine_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (Index("idx_training_alert_type", "related_alert_type"),)
