from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PredictionJob(Base):
    __tablename__ = "prediction_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), index=True, nullable=False)
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    input_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("prediction_jobs.id"), index=True, nullable=False)
    sample_index: Mapped[int] = mapped_column(Integer, nullable=False)
    input_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    prediction_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
