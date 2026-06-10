"""AI privacy confirmation audit table."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIPrivacyConfirmation(Base):
    __tablename__ = "ai_privacy_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    privacy_scan_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    has_privacy_risks: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
