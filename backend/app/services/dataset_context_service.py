"""Service layer for dataset context CRUD and prompt context building."""

from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models.dataset import Dataset
from app.db_models.dataset_context import DatasetContext
from app.db_models.user import User


def _check_dataset_owner(db: Session, current_user: User, dataset_id: int) -> Dataset:
    """Ensure the dataset exists and belongs to the current user."""
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found",
        )
    return dataset


def get_context(db: Session, current_user: User, dataset_id: int) -> DatasetContext | None:
    _check_dataset_owner(db, current_user, dataset_id)
    return db.scalar(
        select(DatasetContext).where(DatasetContext.dataset_id == dataset_id),
    )


def save_context(
    db: Session,
    current_user: User,
    dataset_id: int,
    payload: Mapping[str, Any],
) -> DatasetContext:
    _check_dataset_owner(db, current_user, dataset_id)
    existing = get_context(db, current_user, dataset_id)

    if existing is not None:
        for field in (
            "dataset_source",
            "scenario_description",
            "inclusion_criteria",
            "exclusion_criteria",
            "feature_descriptions",
            "target_descriptions",
            "usage_notes",
        ):
            if field in payload:
                setattr(existing, field, payload[field])
        db.commit()
        db.refresh(existing)
        return existing

    context = DatasetContext(
        user_id=current_user.id,
        dataset_id=dataset_id,
        **{key: payload.get(key) for key in (
            "dataset_source",
            "scenario_description",
            "inclusion_criteria",
            "exclusion_criteria",
            "feature_descriptions",
            "target_descriptions",
            "usage_notes",
        )},
    )
    db.add(context)
    db.commit()
    db.refresh(context)
    return context


def get_dataset_context_for_prompt(
    db: Session,
    current_user: User,
    dataset_id: int,
) -> dict[str, Any]:
    """Return a flattened dict suitable for {dataset_context} prompt variable.

    Returns an empty dict when no context exists (safe for _safe_format).
    """
    ctx = get_context(db, current_user, dataset_id)
    if ctx is None:
        return {}
    return {
        "dataset_source": ctx.dataset_source or "",
        "scenario_description": ctx.scenario_description or "",
        "inclusion_criteria": ctx.inclusion_criteria or "",
        "exclusion_criteria": ctx.exclusion_criteria or "",
        "feature_descriptions": ctx.feature_descriptions or {},
        "target_descriptions": ctx.target_descriptions or {},
        "usage_notes": ctx.usage_notes or "",
    }
