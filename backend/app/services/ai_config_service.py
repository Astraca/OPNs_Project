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
    "你接收的是机器学习算法的输入或输出数据。"
)


# ── AI Config CRUD ────────────────────────────────────────────────────────────

def list_ai_configs(db: Session, current_user: User) -> list[AIConfig]:
    stmt = select(AIConfig).where(AIConfig.user_id == current_user.id).order_by(AIConfig.created_at.desc())
    return list(db.scalars(stmt).all())


def create_ai_config(db: Session, current_user: User, payload: dict) -> AIConfig:
    api_key = str(payload.get("api_key", "")).strip()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="API key is required")
    _check_duplicate_config_name(db, current_user, str(payload["name"]))
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
    if "name" in payload:
        _check_duplicate_config_name(db, current_user, str(payload["name"]), exclude_id=config.id)
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


def _check_duplicate_config_name(
    db: Session,
    current_user: User,
    name: str,
    exclude_id: int | None = None,
) -> None:
    statement = select(AIConfig).where(
        AIConfig.user_id == current_user.id,
        AIConfig.name == name,
    )
    if exclude_id is not None:
        statement = statement.where(AIConfig.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"配置名称 '{name}' 已存在，请使用其他配置名称",
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
            "请分析以下 医疗 研究数据集摘要。系统只提交结构化摘要，不提交原始逐行数据或图片。\n"
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
            "数据集背景：\n{dataset_context}\n\n"
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
    "field_analysis": {
        "name": "字段分析（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下字段统计摘要、字段含义、目标变量信息和隐私扫描结果，对每个字段给出建模处理建议。\n\n"
            "字段统计摘要：\n{field_statistics}\n\n"
            "字段含义说明：\n{feature_descriptions}\n\n"
            "目标变量：\n{target_columns}\n\n"
            "目标变量含义：\n{target_descriptions}\n\n"
            "隐私风险扫描结果：\n{privacy_scan_result}\n\n"
            "要求：\n"
            "1. 对每个字段给出建议类型，必须从以下枚举值中选择："
            "keep、ignore、remove、de_identify、impute_and_keep、standardize_and_keep、"
            "encode_and_keep、check_for_leakage、manual_review\n"
            "2. 对疑似身份标识符给出 remove 或 de_identify 建议\n"
            "3. 对高缺失字段给出 ignore 或 impute_and_keep 建议\n"
            "4. 对疑似目标泄漏字段给出 check_for_leakage 建议\n"
            "5. 对医学敏感字段只说明可能的建模价值，不输出临床结论\n"
            "6. 所有建议只能作为参考，最终由用户确认\n\n"
            "请只输出 JSON 数组，不要包含任何其他文本：\n"
            '[\n'
            '  {{\n'
            '    "field": "字段名",\n'
            '    "recommendation": "keep",\n'
            '    "reason": "建议原因",\n'
            '    "risk_level": "low",\n'
            '    "requires_user_confirmation": false\n'
            '  }}\n'
            ']\n'
        ),
    },
    "training_config_suggestion": {
        "name": "训练配置建议（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下数据集摘要、字段分析结果、标签分布和用户场景说明，给出机器学习模型训练配置建议。\n\n"
            "数据集摘要：\n{dataset_profile}\n\n"
            "字段分析结果：\n{field_recommendations}\n\n"
            "目标变量：\n{target_columns}\n\n"
            "标签分布：\n{label_distribution}\n\n"
            "用户场景说明：\n{dataset_context}\n\n"
            "可选模型：{available_models}\n"
            "可选 OPNs 配对方式：{available_pairing_methods}\n\n"
            "要求：\n"
            "1. 给出任务类型建议\n"
            "2. 给出目标变量设置建议\n"
            "3. 给出输入特征选择建议（包含 exclude 列表）\n"
            "4. 给出缺失值处理、标准化和编码建议\n"
            "5. 给出 OPNs 配对方式建议和算法推荐\n"
            "6. 给出 SVM/SVR 参数初始建议\n"
            "7. 指出类别不平衡和样本量等风险\n"
            "8. 所有建议必须由用户最终确认\n"
            "9. 不输出临床诊断或治疗建议\n\n"
            "请只输出 JSON，不要包含任何其他文本：\n"
            "{{\n"
            '  "task_suggestion": {{\n'
            '    "task_type": "classification",\n'
            '    "target_columns": ["M","E","S","T","C"],\n'
            '    "reason": "..."\n'
            '  }},\n'
            '  "feature_suggestion": {{\n'
            '    "include": ["egfr","scr","proteinuria"],\n'
            '    "exclude": ["patient_id"],\n'
            '    "manual_review": ["visit_date"]\n'
            '  }},\n'
            '  "preprocessing_suggestion": {{\n'
            '    "missing_strategy": "median_for_numeric",\n'
            '    "scaling": true,\n'
            '    "encoding": "label_encoding_or_one_hot"\n'
            '  }},\n'
            '  "model_suggestion": {{\n'
            '    "primary_model": "OPNs-SVM",\n'
            '    "baseline_models": ["SVM","RandomForest"],\n'
            '    "kernel": "rbf",\n'
            '    "pairing_method": "correlation_greedy",\n'
            '    "test_size": 0.2,\n'
            '    "metrics": ["accuracy","precision","recall","f1"]\n'
            '  }},\n'
            '  "warnings": ["E1 样本量较少，建议关注 Recall 和 F1-score。"]\n'
            '}}\n'
        ),
    },
    "batch_prediction_analysis": {
        "name": "批量预测分析（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下批量预测结果摘要，生成批量预测结果分析。\n\n"
            "数据集背景：\n{dataset_context}\n\n"
            "批量预测摘要：\n{batch_prediction_summary}\n\n"
            "预测标签分布：\n{predicted_label_distribution}\n\n"
            "模型整体指标：\n{model_metrics_summary}\n\n"
            "要求：\n"
            "1. 总结批量预测样本数量\n"
            "2. 分析预测标签分布\n"
            "3. 判断是否出现明显偏向某一类别的情况\n"
            "4. 结合模型性能说明结果可信边界\n"
            "5. 指出需要进一步人工复核的部分\n"
            "6. 不输出临床诊断、治疗建议或用药建议\n\n"
            "输出格式：\n"
            "一、批量预测总体情况\n"
            "二、预测标签分布\n"
            "三、可能的模型偏向\n"
            "四、需要关注的不确定性\n"
            "五、后续复核建议\n"
            "六、科研用途声明"
        ),
    },
    "opns_pairing_analysis": {
        "name": "OPNs 配对分析（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下 OPNs 特征配对信息、模型指标和基线模型对比，解释当前 OPNs 特征构造可能对模型表现产生的影响。\n\n"
            "数据集背景：\n{dataset_context}\n\n"
            "OPNs 配置：\n{opns_config}\n\n"
            "特征配对列表：\n{pairing_summary}\n\n"
            "模型指标：\n{model_metrics}\n\n"
            "基线模型对比：\n{baseline_comparison}\n\n"
            "要求：\n"
            "1. 解释当前配对方式的基本含义\n"
            "2. 说明该配对方式可能如何影响结构特征表达\n"
            "3. 结合模型指标分析 OPNs-SVM/SVR 相比基线模型的变化\n"
            "4. 对提升或下降给出谨慎分析\n"
            "5. 不得将模型提升解释为医学因果关系\n"
            "6. 不得输出临床诊断或治疗建议\n\n"
            "输出格式：\n"
            "一、OPNs 配对方式说明\n"
            "二、结构特征表达分析\n"
            "三、与基线模型对比\n"
            "四、可能原因与局限性\n"
            "五、后续实验建议\n"
            "六、科研用途声明"
        ),
    },
    "chart_interpretation": {
        "name": "图表解读（默认）",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "user_prompt": (
            "请根据以下图表对应的结构化数据，对该图表进行科研分析说明。\n\n"
            "图表类型：{chart_type}\n"
            "图表标题：{chart_title}\n"
            "图表数据摘要：{chart_data_summary}\n"
            "数据集背景：{dataset_context}\n\n"
            "要求：\n"
            "1. 说明图表展示的核心现象\n"
            "2. 说明该现象对数据分析或模型训练的影响\n"
            "3. 指出需要注意的局限性\n"
            "4. 不输出临床诊断、治疗建议或用药建议\n\n"
            "输出格式：\n"
            "一、图表主要信息\n"
            "二、可能影响\n"
            "三、注意事项\n"
            "四、科研用途声明"
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
