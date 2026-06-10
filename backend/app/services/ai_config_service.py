from fastapi import HTTPException, status
import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db_models.ai_config import AIConfig, PromptTemplate
from app.db_models.user import User


# ── Pre-configured provider presets ───────────────────────────────────────────

PROVIDER_PRESETS: dict[str, dict] = {
    "deepseek": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "api_base": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "qwen": {
        "name": "Qwen (通义千问)",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "api_base": "https://api.anthropic.com/v1",
        "default_model": "claude-sonnet-4-20250514",
    },
    "openai": {
        "name": "OpenAI / GPT",
        "api_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
    "ollama": {
        "name": "Ollama (本地)",
        "api_base": "http://localhost:11434/v1",
        "default_model": "llama3",
    },
    "custom": {
        "name": "自定义",
        "api_base": "",
        "default_model": "",
    },
}

DEFAULT_SYSTEM_PROMPT = (
    "你是一个医学数据分析助手，仅用于科研和教育目的。"
    "你的回答不构成临床诊断、治疗建议或用药建议。"
    "请基于提供的数据摘要给出客观、准确的分析。"
)


# ── AI Config CRUD ────────────────────────────────────────────────────────────

def list_ai_configs(db: Session, current_user: User) -> list[AIConfig]:
    stmt = select(AIConfig).where(AIConfig.user_id == current_user.id).order_by(AIConfig.created_at.desc())
    return list(db.scalars(stmt).all())


def create_ai_config(db: Session, current_user: User, payload: dict) -> AIConfig:
    api_key = str(payload.get("api_key", "")).strip()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key is required")
    _check_duplicate_model_name(db, current_user, str(payload["model_name"]))
    is_active = bool(payload.get("is_active", False))
    # Deactivate other configs if this one is active
    if is_active:
        db.execute(
            update(AIConfig)
            .where(AIConfig.user_id == current_user.id)
            .values(is_active=False)
        )
    config = AIConfig(
        user_id=current_user.id,
        name=payload["name"],
        provider=payload.get("provider", "custom"),
        api_base=payload["api_base"],
        api_key=api_key,
        model_name=payload["model_name"],
        is_active=is_active,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_ai_config(db: Session, current_user: User, config_id: int, payload: dict) -> AIConfig:
    config = _get_ai_config(db, current_user, config_id)
    if "model_name" in payload:
        _check_duplicate_model_name(db, current_user, str(payload["model_name"]), exclude_id=config.id)
    if payload.get("is_active"):
        db.execute(
            update(AIConfig)
            .where(AIConfig.user_id == current_user.id)
            .values(is_active=False)
        )
    for field in ("name", "provider", "api_base", "api_key", "model_name", "is_active"):
        if field in payload:
            if field == "api_key" and not str(payload[field]).strip():
                continue
            setattr(config, field, payload[field])
    if "is_active" in payload and payload["is_active"] is False:
        config.is_active = False
    db.commit()
    db.refresh(config)
    return config


def delete_ai_config(db: Session, current_user: User, config_id: int) -> None:
    config = _get_ai_config(db, current_user, config_id)
    db.delete(config)
    db.commit()


async def test_ai_config(db: Session, current_user: User, config_id: int) -> dict:
    config = _get_ai_config(db, current_user, config_id)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if config.provider == "claude":
        headers["x-api-key"] = config.api_key
        headers["anthropic-version"] = "2023-06-01"
        body = {
            "model": config.model_name,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "Reply with OK."}],
        }
        api_url = f"{config.api_base.rstrip('/')}/messages"
    else:
        headers["Authorization"] = f"Bearer {config.api_key}"
        body = {
            "model": config.model_name,
            "temperature": 0,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "Reply with OK."}],
        }
        api_url = f"{config.api_base.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(api_url, headers=headers, json=body)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = _extract_ai_error_message(exc.response) if exc.response is not None else str(exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI 配置测试失败：{detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI 配置测试失败：{type(exc).__name__}") from exc

    return {"ok": True, "message": "AI 配置测试成功"}


def _extract_ai_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:500] or response.reason_phrase

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("detail") or error.get("type")
            if message:
                return str(message)
        for key in ("message", "detail", "error_description"):
            if data.get(key):
                return str(data[key])
    return response.reason_phrase or "Unknown error"


def _check_duplicate_model_name(
    db: Session,
    current_user: User,
    model_name: str,
    exclude_id: int | None = None,
) -> None:
    statement = select(AIConfig).where(
        AIConfig.user_id == current_user.id,
        AIConfig.model_name == model_name,
    )
    if exclude_id is not None:
        statement = statement.where(AIConfig.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"模型名称 '{model_name}' 已存在，请使用其他模型名称",
        )


def get_active_config(db: Session, current_user: User) -> AIConfig | None:
    return db.scalar(
        select(AIConfig).where(
            AIConfig.user_id == current_user.id,
            AIConfig.is_active == True,  # noqa: E712
        )
    )


def _get_ai_config(db: Session, current_user: User, config_id: int) -> AIConfig:
    config = db.get(AIConfig, config_id)
    if config is None or config.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI config not found")
    return config


# ── Prompt Template CRUD ──────────────────────────────────────────────────────

DEFAULT_TEMPLATES = {
    "dataset_analysis": {
        "name": "数据集分析（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请分析以下 IgAN 研究数据集摘要。系统只提交结构化摘要，不提交原始逐行数据或图片。\n"
            "样本数：{sample_count}\n字段数：{feature_count}\n"
            "目标字段：{target_columns}\n\n"
            "缺失值情况（高缺失字段）：\n{missing_values}\n\n"
            "标签分布：\n{target_distribution}\n\n"
            "完整提交摘要：\n{dataset_context}\n\n"
            "请从数据规模、缺失值处理建议、类别不平衡、字段角色、建模注意事项角度给出分析。"
            "不要给出临床诊断或治疗建议，最后请附上科研用途声明。"
        ),
    },
    "model_analysis": {
        "name": "模型分析（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请分析以下 IgAN 预测模型评估结果。系统提交的是结构化指标和评估数值，不提交图像文件或模型二进制文件。\n"
            "模型名称：{model_name}\n任务类型：{task_type}\n算法：{algorithm}\n"
            "目标字段：{target_columns}\n输入特征数：{feature_count}\n"
            "OPNs 启用：{opns_enabled}\n配对方式：{pairing_method}\n\n"
            "特征摘要：\n{feature_columns}\n\n"
            "超参数：\n{hyperparameters}\n\n"
            "核心指标：\n{metrics}\n\n"
            "评估补充数据（如混淆矩阵、ROC AUC、残差摘要）：\n{evaluation_context}\n\n"
            "完整提交摘要：\n{model_context}\n\n"
            "请从整体表现、各标签差异、可能过拟合/欠拟合风险、类别不平衡影响、局限性和后续改进建议角度给出分析。"
            "不要给出临床诊断或治疗建议，最后请附上科研用途声明。"
        ),
    },
    "prediction_explanation": {
        "name": "预测说明（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请对以下预测结果生成自然语言说明：\n"
            "预测任务类型：{job_type}\n样本预测结果：\n{prediction_summary}\n\n"
            "请说明各标签的含义、置信度的含义、不确定性来源。"
            "不得包含诊断结论或治疗建议。最后请附上科研用途声明。"
        ),
    },
    "dataset_role_suggestions": {
        "name": "字段角色建议（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下数据集字段摘要，建议哪些字段应作为 feature、target 或 ignored。\n"
            "请特别识别姓名、住院号、编号、ID、常量列、全缺失列等不应进入模型的字段。\n"
            "任务类型：{task_type}\n目标字段：{target_columns}\n字段摘要：\n{column_summary}\n\n"
            "请用中文给出分点建议，说明需要调整的字段和原因。"
            "不要给出临床诊断或治疗建议。"
        ),
    },
    "training_suggestions": {
        "name": "训练参数建议（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请基于以下数据集和建模任务摘要，建议模型训练参数。\n"
            "数据集摘要：\n{dataset_context}\n\n"
            "请建议任务类型、算法、测试集比例、是否启用 OPNs、OPNs 配对方式、目标字段检查重点。"
            "如果样本量较小或标签不均衡，请指出风险。不要给出临床诊断或治疗建议。"
        ),
    },
}


def list_prompt_templates(db: Session, current_user: User, template_type: str | None = None) -> list[PromptTemplate]:
    stmt = select(PromptTemplate).where(PromptTemplate.user_id == current_user.id)
    if template_type:
        stmt = stmt.where(PromptTemplate.template_type == template_type)
    stmt = stmt.order_by(PromptTemplate.created_at.desc())
    return list(db.scalars(stmt).all())


def create_prompt_template(db: Session, current_user: User, payload: dict) -> PromptTemplate:
    tmpl = PromptTemplate(
        user_id=current_user.id,
        name=payload["name"],
        template_type=payload["template_type"],
        system_prompt=payload.get("system_prompt", ""),
        user_prompt=payload["user_prompt"],
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


def update_prompt_template(db: Session, current_user: User, template_id: int, payload: dict) -> PromptTemplate:
    tmpl = _get_prompt_template(db, current_user, template_id)
    for field in ("name", "system_prompt", "user_prompt"):
        if field in payload:
            setattr(tmpl, field, payload[field])
    db.commit()
    db.refresh(tmpl)
    return tmpl


def delete_prompt_template(db: Session, current_user: User, template_id: int) -> None:
    tmpl = _get_prompt_template(db, current_user, template_id)
    db.delete(tmpl)
    db.commit()


def get_default_template(template_type: str) -> dict:
    return DEFAULT_TEMPLATES.get(template_type, DEFAULT_TEMPLATES["dataset_analysis"])


def get_prompt_template_for_type(db: Session, current_user: User, template_type: str) -> dict:
    template = db.scalar(
        select(PromptTemplate)
        .where(
            PromptTemplate.user_id == current_user.id,
            PromptTemplate.template_type == template_type,
        )
        .order_by(PromptTemplate.created_at.desc())
        .limit(1)
    )
    if template is None:
        return get_default_template(template_type)
    return {
        "name": template.name,
        "system_prompt": template.system_prompt,
        "user_prompt": template.user_prompt,
    }


def _get_prompt_template(db: Session, current_user: User, template_id: int) -> PromptTemplate:
    tmpl = db.get(PromptTemplate, template_id)
    if tmpl is None or tmpl.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found")
    return tmpl
