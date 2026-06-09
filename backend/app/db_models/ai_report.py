from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIAnalysisReport(Base):
    __tablename__ = "ai_analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id"), nullable=True)
    prediction_job_id: Mapped[int | None] = mapped_column(ForeignKey("prediction_jobs.id"), nullable=True)
    analysis_type: Mapped[str] = mapped_column(String(64), nullable=False)
    input_summary_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
