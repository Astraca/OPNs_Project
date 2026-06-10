from sqlalchemy import select, update
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from app.db_models.ai_config import AIConfig, PromptTemplate
from app.db_models.user import User


# ── Pre-configured provider presets ───────────────────────────────────────────

PROVIDER_PRESETS: dict[str, dict] = {
    "deepseek": {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
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
    # Deactivate other configs if this one is active
    if payload.get("is_active"):
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
        is_active=payload.get("is_active", False),
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_ai_config(db: Session, current_user: User, config_id: int, payload: dict) -> AIConfig:
    config = _get_ai_config(db, current_user, config_id)
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
    db.commit()
    db.refresh(config)
    return config


def delete_ai_config(db: Session, current_user: User, config_id: int) -> None:
    config = _get_ai_config(db, current_user, config_id)
    db.delete(config)
    db.commit()


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
