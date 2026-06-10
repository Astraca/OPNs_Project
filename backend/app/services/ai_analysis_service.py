import json
from collections.abc import Mapping
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import get_settings
from app.db_models.ai_report import AIAnalysisReport
from app.db_models.ml_model import ModelMetric
from app.db_models.prediction import PredictionJob, PredictionResult
from app.db_models.user import User
from app.schemas.prediction_schema import RESEARCH_DISCLAIMER
from app.services.ai_config_service import get_active_config, get_prompt_template_for_type
from app.services.dataset_service import get_dataset, get_dataset_columns, get_missing_values_chart, get_profile
from app.services.training_service import get_model
from app.utils.igan_fields import display_target_name


# ── Forbidden content patterns ────────────────────────────────────────────────

FORBIDDEN_PRESCRIPTIVE_PATTERNS = [
    "建议用药", "推荐治疗方案", "建议剂量", "临床诊断为",
    "recommended treatment", "prescribe", "dosage recommendation",
    "确诊为", "必须治疗", "立即治疗", "临床处置",
    "药物剂量", "替代医生判断", "可以排除疾病", "可以确认病变",
]


def _validate_ai_response(text: str) -> str:
    """Validate AI output for medical safety boundaries.

    Ensures the disclaimer is present and flags potentially dangerous content.
    """
    text = text.strip()

    # Ensure research disclaimer
    if RESEARCH_DISCLAIMER not in text:
        text = text + "\n\n" + RESEARCH_DISCLAIMER

    # Check for forbidden prescriptive patterns
    for pattern in FORBIDDEN_PRESCRIPTIVE_PATTERNS:
        if pattern in text:
            text += (
                "\n\n[系统提示] AI 输出包含可能被误解为临床建议的表述，"
                "请仅用于科研目的。实际医学判断应由具有资质的临床医生完成。"
            )
            break

    return text


def _safe_format(template: str, values: Mapping[str, Any]) -> str:
    class SafeVars(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return template.format_map(SafeVars({key: str(value) for key, value in values.items()}))


async def _call_llm(
    db: Session,
    current_user: User,
    template_type: str,
    prompt_vars: dict[str, Any],
) -> str:
    """Call the configured LLM.

    AI_MODE=mock is kept only as an explicit local-development escape hatch.
    In normal use, an enabled AI config is required and API failures are surfaced
    to the caller instead of being silently replaced by template text.
    """
    config = get_active_config(db, current_user)
    settings = get_settings()

    if settings.ai_mode == "mock":
        return _generate_mock(template_type, prompt_vars)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在系统设置 - AI 配置中添加并启用一个 AI 模型配置",
        )

    template = get_prompt_template_for_type(db, current_user, template_type)
    system_prompt = _safe_format(template.get("system_prompt", ""), prompt_vars)
    user_prompt = _safe_format(template["user_prompt"], prompt_vars)

    # Determine auth header based on provider
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if config.provider == "claude":
        headers["x-api-key"] = config.api_key
        headers["anthropic-version"] = "2023-06-01"
    else:
        headers["Authorization"] = f"Bearer {config.api_key}"

    # Build request body (OpenAI-compatible format by default)
    if config.provider == "claude":
        body: dict[str, Any] = {
            "model": config.model_name,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        api_url = f"{config.api_base.rstrip('/')}/messages"
    else:
        body = {
            "model": config.model_name,
            "temperature": 0.3,
            "max_tokens": 2048,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        api_url = f"{config.api_base.rstrip('/')}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(api_url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

            if config.provider == "claude":
                raw = data["content"][0]["text"]
            else:
                raw = data["choices"][0]["message"]["content"]
            return _validate_ai_response(raw)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 模型接口返回错误：{detail}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 模型调用失败：{type(exc).__name__}",
        ) from exc
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 模型响应格式无法解析，请检查提供商和 API 地址配置",
        ) from exc


def _json_for_prompt(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _feature_preview(feature_columns: list[str], limit: int = 30) -> dict[str, Any]:
    return {
        "count": len(feature_columns),
        "columns": feature_columns[:limit],
        "truncated": len(feature_columns) > limit,
    }


def _column_role_recommendation(column: Any, total_rows: int, target_columns: set[str]) -> dict[str, Any]:
    name = column.column_name
    lower_name = name.lower()
    identifier_markers = ["name", "姓名", "住院号", "编号", "患者id", "病历号", "record_id", "patient_id"]
    is_identifier = (
        lower_name in {"id", "uuid"}
        or lower_name.endswith("_id")
        or lower_name.endswith("-id")
        or any(marker in lower_name for marker in identifier_markers)
    )
    if name in target_columns:
        role = "target"
        reason = "该字段已被识别为目标字段"
    elif is_identifier:
        role = "ignored"
        reason = "疑似身份标识或编号字段，不应作为预测特征"
    elif column.missing_count >= total_rows:
        role = "ignored"
        reason = "字段全缺失"
    elif column.unique_count <= 1:
        role = "ignored"
        reason = "字段为常量或近似常量"
    elif (column.missing_count / total_rows >= 0.5) if total_rows else False:
        role = "ignored"
        reason = "缺失率较高，建模前建议谨慎使用"
    else:
        role = "feature"
        reason = "可作为候选预测特征"
    return {
        "column_name": name,
        "current_role": column.role,
        "recommended_role": role,
        "reason": reason,
    }


def _metric_summary(metrics: list[ModelMetric]) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = {}
    for metric in metrics:
        target = display_target_name(metric.target_name or "overall")
        grouped.setdefault(target, {})[metric.metric_name] = round(metric.metric_value, 4)
    return grouped


def _model_evaluation_context(db: Session, current_user: User, model_id: int, task_type: str) -> dict[str, Any]:
    try:
        if task_type == "regression":
            from app.services.evaluation_service import build_residuals

            residuals = build_residuals(db, current_user, model_id)
            values = residuals.residuals
            return {
                "residual_summary": {
                    "count": len(values),
                    "mean": round(sum(values) / len(values), 4) if values else None,
                    "max_abs": round(max((abs(v) for v in values), default=0), 4),
                    "sample": values[:20],
                }
            }

        from app.services.evaluation_service import build_confusion_matrices, build_roc_curves

        confusion = [
            item.model_dump()
            for item in build_confusion_matrices(db, current_user, model_id)
        ]
        roc_summary = [
            {
                "target_name": item.target_name,
                "auc_values": [round(curve.auc, 4) for curve in item.curves if curve.auc is not None],
            }
            for item in build_roc_curves(db, current_user, model_id)
        ]
        return {"confusion_matrices": confusion, "roc_summary": roc_summary}
    except Exception as exc:
        return {"evaluation_artifacts_error": f"{type(exc).__name__}: {exc}"}


def _generate_mock(template_type: str, prompt_vars: dict[str, Any]) -> str:
    """Generate analysis text using templates (no external API)."""
    if template_type == "dataset_analysis":
        return "\n".join([
            f"数据集包含 {prompt_vars.get('sample_count', '?')} 条样本、{prompt_vars.get('feature_count', '?')} 个字段。",
            f"当前目标字段为：{prompt_vars.get('target_columns', '暂未识别')}。",
            "建模前建议确认 ignored 字段是否已排除。",
            "若某些标签分布明显不均衡，模型评估时应重点关注 Precision、Recall 和 F1。",
            RESEARCH_DISCLAIMER,
        ])
    if template_type == "model_analysis":
        return "\n".join([
            f"模型使用 {prompt_vars.get('algorithm', '?')} 算法。",
            f"输入特征数为 {prompt_vars.get('feature_count', '?')}。",
            "不同标签表现差异应结合样本量、类别不平衡和缺失值情况理解。",
            "该分析不代表医学诊断能力，只用于模型验证和科研讨论。",
            RESEARCH_DISCLAIMER,
        ])
    return "\n".join([
        f"预测任务共生成 {prompt_vars.get('sample_count', '?')} 条预测结果。",
        "单个标签的概率仅表示模型在当前训练数据和特征处理流程下的分类置信度。",
        "该说明不包含诊断结论、治疗建议或用药建议。",
        RESEARCH_DISCLAIMER,
    ])


async def generate_dataset_analysis(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    profile = get_profile(db, current_user, dataset_id)
    missing = get_missing_values_chart(db, current_user, dataset_id)
    dataset = profile["dataset"]
    high_missing = [
        item for item in missing["items"]
        if item["missing_rate"] >= 0.1
    ][:5]
    summary = {
        "sample_count": dataset.sample_count,
        "feature_count": dataset.feature_count,
        "target_columns": dataset.target_columns,
        "missing_values": high_missing,
        "target_distribution": profile["target_distribution"],
        "submitted_to_ai": [
            "样本数、字段数、目标字段",
            "缺失率最高的字段摘要",
            "目标标签分布",
            "不上传原始逐行数据或图像",
        ],
    }

    prompt_vars = {
        "sample_count": str(dataset.sample_count),
        "feature_count": str(dataset.feature_count),
        "target_columns": ", ".join(map(display_target_name, dataset.target_columns)) or "暂未识别",
        "missing_values": _json_for_prompt(high_missing),
        "target_distribution": _json_for_prompt(profile["target_distribution"]),
        "dataset_context": _json_for_prompt(summary),
    }
    text = await _call_llm(db, current_user, "dataset_analysis", prompt_vars)
    return save_ai_report(db, current_user, "dataset_analysis", text, summary, dataset_id=dataset_id)


async def generate_dataset_role_suggestions(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    dataset = get_dataset(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset_id)
    total_rows = dataset.sample_count or 0
    target_set = set(dataset.target_columns)
    column_summary = [
        {
            "column_name": column.column_name,
            "data_type": column.data_type,
            "current_role": column.role,
            "missing_count": column.missing_count,
            "missing_rate": round(column.missing_count / total_rows, 4) if total_rows else None,
            "unique_count": column.unique_count,
            "mean": column.mean,
            "std": column.std,
            "min_value": column.min_value,
            "max_value": column.max_value,
        }
        for column in columns
    ]
    recommendations = [
        _column_role_recommendation(column, total_rows, target_set)
        for column in columns
    ]
    summary = {
        "dataset_name": dataset.name,
        "task_type": dataset.task_type,
        "sample_count": dataset.sample_count,
        "feature_count": dataset.feature_count,
        "target_columns": dataset.target_columns,
        "column_summary": column_summary,
        "rule_based_recommendations": recommendations,
        "submitted_to_ai": [
            "字段名称、类型、当前角色",
            "缺失数/缺失率、唯一值数量、基础数值统计",
            "自动规则建议",
            "不上传原始逐行数据",
        ],
    }
    prompt_vars = {
        "task_type": dataset.task_type,
        "target_columns": ", ".join(map(display_target_name, dataset.target_columns)) or "暂未识别",
        "column_summary": _json_for_prompt({
            "columns": column_summary,
            "rule_based_recommendations": recommendations,
        }),
    }
    text = await _call_llm(db, current_user, "dataset_role_suggestions", prompt_vars)
    return save_ai_report(
        db,
        current_user,
        "dataset_role_suggestions",
        text,
        summary,
        dataset_id=dataset_id,
    )


async def generate_training_suggestions(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    dataset = get_dataset(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset_id)
    total_rows = dataset.sample_count or 0
    role_counts = {
        "feature": sum(1 for column in columns if column.role == "feature"),
        "target": sum(1 for column in columns if column.role == "target"),
        "ignored": sum(1 for column in columns if column.role == "ignored"),
    }
    high_missing = [
        {
            "column_name": column.column_name,
            "role": column.role,
            "missing_rate": round(column.missing_count / total_rows, 4) if total_rows else None,
        }
        for column in columns
        if total_rows and column.missing_count / total_rows >= 0.1
    ][:10]
    suggested = {
        "algorithm": "OPNs-SVR" if dataset.task_type == "regression" else "OPNs-SVM",
        "test_size": 0.2 if (dataset.sample_count or 0) >= 50 else 0.3,
        "pairing_method": "correlation_greedy" if role_counts["feature"] >= 6 else "adjacent",
        "notes": [
            "样本量较小时建议关注交叉验证或重复划分稳定性",
            "目标字段应在训练前确认，编号/身份标识字段应忽略",
        ],
    }
    summary = {
        "dataset_name": dataset.name,
        "task_type": dataset.task_type,
        "sample_count": dataset.sample_count,
        "feature_count": dataset.feature_count,
        "target_columns": dataset.target_columns,
        "role_counts": role_counts,
        "high_missing_columns": high_missing,
        "rule_based_suggestion": suggested,
    }
    prompt_vars = {"dataset_context": _json_for_prompt(summary)}
    text = await _call_llm(db, current_user, "training_suggestions", prompt_vars)
    return save_ai_report(
        db,
        current_user,
        "training_suggestions",
        text,
        summary,
        dataset_id=dataset_id,
    )


async def generate_model_analysis(db: Session, current_user: User, model_id: int) -> AIAnalysisReport:
    from app.db_models.dataset_context import DatasetContext

    model = get_model(db, current_user, model_id)
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    metrics = list(db.scalars(statement).all())
    grouped = _metric_summary(metrics)

    f1_values = [values.get("f1", 0) for values in grouped.values()]
    avg_f1 = round(sum(f1_values) / len(f1_values), 4) if f1_values else 0
    evaluation_context = _model_evaluation_context(db, current_user, model.id, model.task_type)

    # Fetch dataset context for enhanced analysis
    ctx = db.scalar(
        select(DatasetContext).where(DatasetContext.dataset_id == model.dataset_id),
    ) if model.dataset_id else None
    dataset_context = {
        "scenario_description": ctx.scenario_description or "",
        "feature_descriptions": ctx.feature_descriptions or {},
        "target_descriptions": ctx.target_descriptions or {},
    } if ctx else {}

    summary = {
        "model_name": model.model_name,
        "task_type": model.task_type,
        "algorithm": model.algorithm,
        "target_columns": [display_target_name(target) for target in model.target_columns],
        "features": _feature_preview(model.feature_columns),
        "opns_enabled": model.opns_enabled,
        "pairing_method": model.pairing_method,
        "hyperparameters": model.hyperparameters,
        "metrics": grouped,
        "evaluation_context": evaluation_context,
        "submitted_to_ai": [
            "模型名称、任务类型、算法、目标字段",
            "特征数量和前 30 个特征名",
            "训练超参数、OPNs 设置",
            "分类/回归指标",
            "可计算的混淆矩阵、ROC AUC 或残差摘要数值",
            "不上传图像文件或模型二进制文件",
        ],
    }

    prompt_vars = {
        "model_name": model.model_name,
        "task_type": model.task_type,
        "algorithm": model.algorithm,
        "target_columns": ", ".join(map(display_target_name, model.target_columns)),
        "feature_count": str(len(model.feature_columns)),
        "feature_columns": _json_for_prompt(_feature_preview(model.feature_columns)),
        "hyperparameters": _json_for_prompt(model.hyperparameters),
        "opns_enabled": "是" if model.opns_enabled else "否",
        "pairing_method": model.pairing_method or "无",
        "avg_f1": str(avg_f1),
        "metrics": _json_for_prompt(grouped),
        "evaluation_context": _json_for_prompt(evaluation_context),
        "model_context": _json_for_prompt(summary),
        "dataset_context": _json_for_prompt(dataset_context) if dataset_context else "暂未填写数据集背景",
    }
    text = await _call_llm(db, current_user, "model_analysis", prompt_vars)
    return save_ai_report(db, current_user, "model_analysis", text, summary, model_id=model_id)


async def generate_prediction_explanation(db: Session, current_user: User, prediction_job_id: int) -> AIAnalysisReport:
    from app.db_models.dataset_context import DatasetContext

    job = db.get(PredictionJob, prediction_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")
    statement = select(PredictionResult).where(PredictionResult.job_id == job.id).order_by(PredictionResult.sample_index)
    results = list(db.scalars(statement).all())
    first_prediction = results[0].prediction_json if results else {}
    summary = {"job_id": job.id, "job_type": job.job_type, "first_prediction": first_prediction}

    # Fetch dataset context if available
    ctx = None
    if job.model_id:
        model = get_model(db, current_user, job.model_id)
        if model and model.dataset_id:
            ctx = db.scalar(
                select(DatasetContext).where(DatasetContext.dataset_id == model.dataset_id),
            )
    dataset_context = {
        "scenario_description": ctx.scenario_description or "",
        "target_descriptions": ctx.target_descriptions or {},
    } if ctx else {}

    prompt_vars = {
        "job_type": job.job_type,
        "sample_count": str(len(results)),
        "prediction_summary": _json_for_prompt(first_prediction),
        "dataset_context": _json_for_prompt(dataset_context) if dataset_context else "暂未填写",
    }
    text = await _call_llm(db, current_user, "prediction_explanation", prompt_vars)
    return save_ai_report(
        db, current_user, "prediction_explanation", text, summary,
        model_id=job.model_id, prediction_job_id=job.id,
    )


async def generate_batch_prediction_analysis(
    db: Session, current_user: User, prediction_job_id: int,
) -> AIAnalysisReport:
    """Generate analysis for batch prediction results."""
    from collections import Counter

    from app.db_models.dataset_context import DatasetContext

    job = db.get(PredictionJob, prediction_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")

    statement = select(PredictionResult).where(
        PredictionResult.job_id == job.id,
    ).order_by(PredictionResult.sample_index)
    results = list(db.scalars(statement).all())

    # Build prediction distribution summary
    label_distribution: dict[str, Counter] = {}
    for result in results:
        pred = result.prediction_json or {}
        if isinstance(pred, dict):
            if "result" in pred:  # classification
                for target, value in pred["result"].items():
                    label = value.get("label", "?") if isinstance(value, dict) else str(value)
                    label_distribution.setdefault(target, Counter())[label] += 1
            elif "predicted_value" in pred:  # regression
                label_distribution.setdefault("predicted_value", Counter())["count"] += 1

    # Model metrics
    metrics_summary = {}
    if job.model_id:
        model = get_model(db, current_user, job.model_id)
        metrics = db.scalars(
            select(ModelMetric).where(ModelMetric.model_id == model.id),
        ).all()
        metrics_summary = _metric_summary(list(metrics))

        # Dataset context
        ctx = db.scalar(
            select(DatasetContext).where(DatasetContext.dataset_id == model.dataset_id),
        ) if model.dataset_id else None
        dataset_context = {
            "scenario_description": ctx.scenario_description or "",
            "target_descriptions": ctx.target_descriptions or {},
        } if ctx else {}
    else:
        dataset_context = {}

    # Low-confidence samples
    low_confidence_count = 0
    for result in results:
        pred = result.prediction_json or {}
        if isinstance(pred, dict) and "result" in pred:
            probs = [
                v.get("probability", 1) if isinstance(v, dict) else 1
                for v in pred["result"].values()
            ]
            if probs and min(probs) < 0.6:
                low_confidence_count += 1

    summary = {
        "job_id": job.id,
        "job_type": job.job_type,
        "sample_count": len(results),
        "predicted_label_distribution": {k: dict(v) for k, v in label_distribution.items()},
        "model_metrics_summary": metrics_summary,
        "low_confidence_count": low_confidence_count,
    }

    prompt_vars = {
        "batch_prediction_summary": _json_for_prompt({
            "job_type": job.job_type,
            "sample_count": len(results),
            "low_confidence_count": low_confidence_count,
        }),
        "predicted_label_distribution": _json_for_prompt(
            {k: dict(v) for k, v in label_distribution.items()},
        ),
        "model_metrics_summary": _json_for_prompt(metrics_summary),
        "dataset_context": _json_for_prompt(dataset_context) if dataset_context else "暂未填写",
    }
    text = await _call_llm(db, current_user, "batch_prediction_analysis", prompt_vars)
    return save_ai_report(
        db, current_user, "batch_prediction_analysis", text, summary,
        model_id=job.model_id, prediction_job_id=job.id,
    )


async def generate_opns_pairing_analysis(
    db: Session, current_user: User, model_id: int,
) -> AIAnalysisReport:
    """Generate OPNs pairing analysis for a trained model."""
    import os

    from app.db_models.dataset_context import DatasetContext

    model = get_model(db, current_user, model_id)
    if not model.opns_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This model does not use OPNs feature construction.",
        )

    metrics = db.scalars(
        select(ModelMetric).where(ModelMetric.model_id == model.id),
    ).all()
    grouped = _metric_summary(list(metrics))

    # Load transformer to get pairs
    pairs = []
    try:
        from joblib import load
        if model.metadata_file_path and os.path.isfile(model.metadata_file_path):
            model_dir = os.path.dirname(model.metadata_file_path)
            transformer_path = os.path.join(model_dir, "opns_transformer.pkl")
            if os.path.isfile(transformer_path):
                transformer = load(transformer_path)
                pairs = [(str(a), str(b)) for a, b in getattr(transformer, "pairs_", [])]
    except Exception:
        pairs = []

    # Dataset context
    ctx = db.scalar(
        select(DatasetContext).where(DatasetContext.dataset_id == model.dataset_id),
    ) if model.dataset_id else None
    dataset_context = {
        "scenario_description": ctx.scenario_description or "",
        "feature_descriptions": ctx.feature_descriptions or {},
    } if ctx else {}

    summary = {
        "model_name": model.model_name,
        "algorithm": model.algorithm,
        "pairing_method": model.pairing_method,
        "pairs": pairs,
        "pair_count": len(pairs),
        "metrics": grouped,
    }

    prompt_vars = {
        "dataset_context": _json_for_prompt(dataset_context) if dataset_context else "暂未填写",
        "opns_config": _json_for_prompt({
            "algorithm": model.algorithm,
            "pairing_method": model.pairing_method,
            "mapping_config": model.mapping_config or {},
        }),
        "pairing_summary": _json_for_prompt({
            "pairing_method": model.pairing_method,
            "pairs": [{"left": a, "right": b} for a, b in pairs],
            "total_pairs": len(pairs),
        }),
        "model_metrics": _json_for_prompt(grouped),
        "baseline_comparison": _json_for_prompt({"note": "与同一数据集上标准 SVM/SVR 比较"}),
    }
    text = await _call_llm(db, current_user, "opns_pairing_analysis", prompt_vars)
    return save_ai_report(db, current_user, "opns_pairing_analysis", text, summary, model_id=model_id)


async def generate_chart_interpretation(
    db: Session, current_user: User, payload: dict,
) -> AIAnalysisReport:
    """Generate natural language interpretation of a chart from its data."""
    chart_type = payload.get("chart_type", "")
    chart_title = payload.get("chart_title", "")
    chart_data = payload.get("chart_data", {})
    context = payload.get("context", {})

    summary = {
        "chart_type": chart_type,
        "chart_title": chart_title,
        "chart_data": chart_data,
    }

    prompt_vars = {
        "chart_type": chart_type,
        "chart_title": chart_title,
        "chart_data_summary": _json_for_prompt(chart_data),
        "dataset_context": _json_for_prompt(context) if context else "暂未填写",
    }
    text = await _call_llm(db, current_user, "chart_interpretation", prompt_vars)
    return save_ai_report(db, current_user, "chart_interpretation", text, summary)


def get_latest_dataset_analysis(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    statement = (
        select(AIAnalysisReport)
        .where(
            AIAnalysisReport.user_id == current_user.id,
            AIAnalysisReport.dataset_id == dataset_id,
            AIAnalysisReport.analysis_type == "dataset_analysis",
        )
        .order_by(AIAnalysisReport.created_at.desc())
        .limit(1)
    )
    report = db.scalar(statement)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI analysis found for this dataset. Generate one first via POST.",
        )
    return report


def get_latest_model_analysis(db: Session, current_user: User, model_id: int) -> AIAnalysisReport:
    statement = (
        select(AIAnalysisReport)
        .where(
            AIAnalysisReport.user_id == current_user.id,
            AIAnalysisReport.model_id == model_id,
            AIAnalysisReport.analysis_type == "model_analysis",
        )
        .order_by(AIAnalysisReport.created_at.desc())
        .limit(1)
    )
    report = db.scalar(statement)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AI analysis found for this model. Generate one first via POST.",
        )
    return report


def save_ai_report(
    db: Session,
    current_user: User,
    analysis_type: str,
    generated_text: str,
    summary: dict,
    dataset_id: int | None = None,
    model_id: int | None = None,
    prediction_job_id: int | None = None,
) -> AIAnalysisReport:
    report = AIAnalysisReport(
        user_id=current_user.id,
        dataset_id=dataset_id,
        model_id=model_id,
        prediction_job_id=prediction_job_id,
        analysis_type=analysis_type,
        input_summary_json=summary,
        generated_text=generated_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


async def generate_field_analysis(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    """Generate AI field-level recommendations with structured JSON output."""
    import json
    import re

    from app.ai.privacy_guard import scan_dataset
    from app.db_models.ai_field import AIFieldRecommendation
    from app.db_models.dataset_context import DatasetContext

    dataset = get_dataset(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset_id)
    total_rows = dataset.sample_count or 0

    # Build column statistics
    col_stats = [
        {
            "column_name": col.column_name,
            "data_type": col.data_type,
            "current_role": col.role,
            "missing_count": col.missing_count,
            "missing_rate": round(col.missing_count / total_rows, 4) if total_rows else None,
            "unique_count": col.unique_count,
            "mean": col.mean,
            "std": col.std,
            "min_value": col.min_value,
            "max_value": col.max_value,
        }
        for col in columns
    ]

    # Run privacy scan
    privacy_result = scan_dataset(columns, total_rows)

    # Fetch dataset context if available
    ctx = db.scalar(
        select(DatasetContext).where(DatasetContext.dataset_id == dataset.id),
    )
    feature_desc = ctx.feature_descriptions if ctx else {}
    target_desc = ctx.target_descriptions if ctx else {}

    summary = {
        "dataset_name": dataset.name,
        "task_type": dataset.task_type,
        "sample_count": total_rows,
        "target_columns": dataset.target_columns,
        "column_statistics": col_stats,
        "privacy_scan": privacy_result,
        "feature_descriptions": feature_desc,
        "target_descriptions": target_desc,
    }

    prompt_vars = {
        "field_statistics": _json_for_prompt(col_stats),
        "feature_descriptions": _json_for_prompt(feature_desc),
        "target_columns": ", ".join(dataset.target_columns) if dataset.target_columns else "暂未设置",
        "target_descriptions": _json_for_prompt(target_desc),
        "privacy_scan_result": _json_for_prompt({
            "classifications": [
                c for c in privacy_result["classifications"]
                if c["classification"] != "normal_modeling"
            ],
            "risk_summary": privacy_result["risk_summary"],
        }),
    }

    text = await _call_llm(db, current_user, "field_analysis", prompt_vars)

    # Parse structured JSON from AI output
    recommendations = _parse_field_recommendations(text)

    # Delete old recommendations for this dataset
    old = db.scalars(
        select(AIFieldRecommendation).where(
            AIFieldRecommendation.dataset_id == dataset_id,
            AIFieldRecommendation.user_id == current_user.id,
        ),
    ).all()
    for row in old:
        db.delete(row)

    # Save new recommendations
    for rec in recommendations:
        db.add(AIFieldRecommendation(
            user_id=current_user.id,
            dataset_id=dataset_id,
            field=rec["field"],
            recommendation=rec["recommendation"],
            reason=rec["reason"],
            risk_level=rec.get("risk_level", "low"),
            requires_user_confirmation=rec.get("requires_user_confirmation", False),
        ))

    report = save_ai_report(db, current_user, "field_analysis", text, summary, dataset_id=dataset_id)
    db.commit()
    return report


def _parse_field_recommendations(text: str) -> list[dict]:
    """Extract structured field recommendations from AI output."""
    import json
    import re

    VALID_RECOMMENDATIONS = {
        "keep", "ignore", "remove", "de_identify",
        "impute_and_keep", "standardize_and_keep",
        "encode_and_keep", "check_for_leakage", "manual_review",
    }
    VALID_RISK_LEVELS = {"high", "medium", "low"}

    # Try to extract JSON array from the response
    # Strip markdown code blocks
    clean = re.sub(r"^```(?:json)?\s*", "", text.strip())
    clean = re.sub(r"\s*```$", "", clean)

    try:
        parsed = json.loads(clean)
        if isinstance(parsed, list):
            result = []
            for item in parsed:
                if not isinstance(item, dict) or "field" not in item:
                    continue
                rec = item.get("recommendation", "manual_review")
                if rec not in VALID_RECOMMENDATIONS:
                    rec = "manual_review"
                risk = item.get("risk_level", "low")
                if risk not in VALID_RISK_LEVELS:
                    risk = "low"
                result.append({
                    "field": str(item["field"]),
                    "recommendation": rec,
                    "reason": str(item.get("reason", "")),
                    "risk_level": risk,
                    "requires_user_confirmation": bool(item.get("requires_user_confirmation", False)),
                })
            return result
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Fallback: try to find JSON array via regex
    match = re.search(r"\[.*\]", clean, re.DOTALL)
    if match:
        try:
            return _parse_field_recommendations(match.group(0))
        except Exception:
            pass

    return []


def get_latest_field_analysis(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
    report = db.scalar(
        select(AIAnalysisReport)
        .where(
            AIAnalysisReport.user_id == current_user.id,
            AIAnalysisReport.dataset_id == dataset_id,
            AIAnalysisReport.analysis_type == "field_analysis",
        )
        .order_by(AIAnalysisReport.created_at.desc())
        .limit(1)
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No field analysis found. Generate one via POST first.",
        )
    return report


def get_field_recommendations(db: Session, current_user: User, dataset_id: int) -> list[dict]:
    """Get the saved AI field recommendations for a dataset."""
    from app.db_models.ai_field import AIFieldRecommendation

    rows = db.scalars(
        select(AIFieldRecommendation)
        .where(
            AIFieldRecommendation.dataset_id == dataset_id,
            AIFieldRecommendation.user_id == current_user.id,
        )
        .order_by(AIFieldRecommendation.id)
    ).all()
    return [
        {
            "id": row.id,
            "field": row.field,
            "recommendation": row.recommendation,
            "reason": row.reason,
            "risk_level": row.risk_level,
            "requires_user_confirmation": row.requires_user_confirmation,
            "user_confirmed": row.user_confirmed,
            "user_modification": row.user_modification,
        }
        for row in rows
    ]


def confirm_field_recommendations(
    db: Session,
    current_user: User,
    dataset_id: int,
    confirmations: list[dict],
) -> dict:
    """Apply user-confirmed field recommendations to dataset columns."""
    from app.db_models.ai_field import AIFieldRecommendation

    # Role mapping from recommendation to dataset column role
    RECOMMENDATION_TO_ROLE: dict[str, str] = {
        "keep": "feature",
        "ignore": "ignored",
        "remove": "ignored",
        "de_identify": "ignored",
        "impute_and_keep": "feature",
        "standardize_and_keep": "feature",
        "encode_and_keep": "feature",
        "check_for_leakage": "ignored",
        "manual_review": None,  # no change
    }

    # Update field recommendation rows
    for item in confirmations:
        field_name = item.get("field", "")
        row = db.scalar(
            select(AIFieldRecommendation).where(
                AIFieldRecommendation.dataset_id == dataset_id,
                AIFieldRecommendation.user_id == current_user.id,
                AIFieldRecommendation.field == field_name,
            ),
        )
        if row is not None:
            row.user_confirmed = item.get("accepted", False)
            row.user_modification = item.get("modification")

    db.commit()

    # Apply accepted recommendations to dataset columns
    accepted_fields = {
        item["field"]: item.get("modification") or item["field"]
        for item in confirmations
        if item.get("accepted")
    }

    if accepted_fields:
        field_recommendations = db.scalars(
            select(AIFieldRecommendation).where(
                AIFieldRecommendation.dataset_id == dataset_id,
                AIFieldRecommendation.user_id == current_user.id,
            ),
        ).all()

        rec_map = {r.field: r.recommendation for r in field_recommendations}

        for col in get_dataset_columns(db, current_user, dataset_id):
            if col.column_name in accepted_fields:
                rec = rec_map.get(col.column_name, "keep")
                new_role = RECOMMENDATION_TO_ROLE.get(rec)
                if new_role and col.role != new_role:
                    col.role = new_role

        db.commit()

    return {"updated_fields": len(accepted_fields)}


async def generate_training_config_suggestion(
    db: Session, current_user: User, dataset_id: int,
) -> AIAnalysisReport:
    """Generate structured training config suggestion with JSON output."""
    import json
    import re

    from app.db_models.ai_field import AIFieldRecommendation
    from app.db_models.dataset_context import DatasetContext

    dataset = get_dataset(db, current_user, dataset_id)
    profile = get_profile(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset_id)

    # Field recommendations
    field_recs = db.scalars(
        select(AIFieldRecommendation).where(
            AIFieldRecommendation.dataset_id == dataset_id,
            AIFieldRecommendation.user_id == current_user.id,
        ),
    ).all()
    field_rec_data = [
        {"field": r.field, "recommendation": r.recommendation, "reason": r.reason}
        for r in field_recs
    ] if field_recs else []

    # Dataset context
    ctx = db.scalar(
        select(DatasetContext).where(DatasetContext.dataset_id == dataset.id),
    )
    dataset_context = {
        "scenario_description": ctx.scenario_description or "",
        "feature_descriptions": ctx.feature_descriptions or {},
        "target_descriptions": ctx.target_descriptions or {},
    } if ctx else {}

    # Available models based on task type
    if dataset.task_type == "regression":
        available_models = "OPNs-SVR, SVR, RandomForest (回归), Ridge"
        available_pairing = "adjacent, random, correlation_greedy"
    else:
        available_models = "OPNs-SVM, SVM, RandomForest (分类), LogisticRegression"
        available_pairing = "adjacent, random, correlation_greedy"

    summary = {
        "dataset_id": dataset.id,
        "task_type": dataset.task_type,
        "sample_count": dataset.sample_count,
        "target_columns": dataset.target_columns,
        "field_recommendations": field_rec_data,
        "dataset_context": dataset_context,
    }

    prompt_vars = {
        "dataset_profile": _json_for_prompt({
            "name": dataset.name,
            "task_type": dataset.task_type,
            "sample_count": dataset.sample_count,
            "feature_count": dataset.feature_count,
            "target_columns": dataset.target_columns,
        }),
        "field_recommendations": _json_for_prompt(field_rec_data),
        "target_columns": ", ".join(dataset.target_columns) if dataset.target_columns else "暂未设置",
        "label_distribution": _json_for_prompt(profile.get("target_distribution", {})),
        "dataset_context": _json_for_prompt(dataset_context) if dataset_context else "暂未填写",
        "available_models": available_models,
        "available_pairing_methods": available_pairing,
    }

    text = await _call_llm(db, current_user, "training_config_suggestion", prompt_vars)

    # Parse structured JSON
    clean = re.sub(r"^```(?:json)?\s*", "", text.strip())
    clean = re.sub(r"\s*```$", "", clean)
    try:
        parsed = json.loads(clean) if isinstance(clean, str) and clean.strip() else {}
    except json.JSONDecodeError:
        parsed = {"raw": text}

    return save_ai_report(
        db, current_user, "training_config_suggestion", text,
        {**summary, "parsed_suggestion": parsed},
        dataset_id=dataset_id,
    )


def get_latest_training_config_suggestion(
    db: Session, current_user: User, dataset_id: int,
) -> AIAnalysisReport:
    report = db.scalar(
        select(AIAnalysisReport)
        .where(
            AIAnalysisReport.user_id == current_user.id,
            AIAnalysisReport.dataset_id == dataset_id,
            AIAnalysisReport.analysis_type == "training_config_suggestion",
        )
        .order_by(AIAnalysisReport.created_at.desc())
        .limit(1)
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No training config suggestion found. Generate one via POST first.",
        )
    return report
