"""AI field recommendation storage — one row per field per analysis run."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIFieldRecommendation(Base):
    __tablename__ = "ai_field_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), index=True, nullable=False)
    field: Mapped[str] = mapped_column(String(255), nullable=False)
    recommendation: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )  # keep/ignore/remove/de_identify/impute_and_keep/standardize_and_keep/encode_and_keep/check_for_leakage/manual_review
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    requires_user_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_confirmed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user_modification: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )
