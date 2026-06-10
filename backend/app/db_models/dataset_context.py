"""Dataset context model for storing dataset background and field descriptions."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DatasetContext(Base):
    __tablename__ = "dataset_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"), index=True, nullable=False, unique=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False,
    )
    dataset_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    inclusion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    exclusion_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_descriptions: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False,
    )
    target_descriptions: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False,
    )
    usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )
