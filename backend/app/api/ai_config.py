from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.ai_config import AIConfig, PromptTemplate
from app.db_models.user import User
from app.dependencies import get_current_user
from app.services import ai_config_service

router = APIRouter(prefix="/api/ai-config", tags=["ai-config"])


# ── Provider presets ──────────────────────────────────────────────────────────

@router.get("/providers")
def list_providers() -> dict:
    return {"providers": ai_config_service.PROVIDER_PRESETS}


# ── AI Configs ────────────────────────────────────────────────────────────────

@router.get("/configs")
def list_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return [cfg_to_dict(c) for c in ai_config_service.list_ai_configs(db, current_user)]


@router.post("/configs", status_code=status.HTTP_201_CREATED)
def create_config(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return cfg_to_dict(ai_config_service.create_ai_config(db, current_user, payload))


@router.put("/configs/{config_id}")
def update_config(
    config_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return cfg_to_dict(ai_config_service.update_ai_config(db, current_user, config_id, payload))


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    ai_config_service.delete_ai_config(db, current_user, config_id)


# ── Prompt Templates ──────────────────────────────────────────────────────────

@router.get("/templates")
def list_templates(
    template_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return [
        tmpl_to_dict(t)
        for t in ai_config_service.list_prompt_templates(db, current_user, template_type)
    ]


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return tmpl_to_dict(ai_config_service.create_prompt_template(db, current_user, payload))


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return tmpl_to_dict(ai_config_service.update_prompt_template(db, current_user, template_id, payload))


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    ai_config_service.delete_prompt_template(db, current_user, template_id)


@router.get("/templates/default/{template_type}")
def get_default_template(template_type: str) -> dict:
    return ai_config_service.get_default_template(template_type)


# ── Serializers ───────────────────────────────────────────────────────────────

def cfg_to_dict(cfg: AIConfig) -> dict:
    return {
        "id": cfg.id,
        "name": cfg.name,
        "provider": cfg.provider,
        "api_base": cfg.api_base,
        "has_api_key": bool(cfg.api_key),
        "model_name": cfg.model_name,
        "is_active": cfg.is_active,
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
    }


def tmpl_to_dict(tmpl: PromptTemplate) -> dict:
    return {
        "id": tmpl.id,
        "name": tmpl.name,
        "template_type": tmpl.template_type,
        "system_prompt": tmpl.system_prompt,
        "user_prompt": tmpl.user_prompt,
        "created_at": tmpl.created_at.isoformat() if tmpl.created_at else None,
    }
