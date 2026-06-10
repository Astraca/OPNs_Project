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
from app.services.dataset_service import get_missing_values_chart, get_profile
from app.services.training_service import get_model
from app.utils.igan_fields import display_target_name


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
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(api_url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

            if config.provider == "claude":
                return data["content"][0]["text"]
            return data["choices"][0]["message"]["content"]
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


async def generate_model_analysis(db: Session, current_user: User, model_id: int) -> AIAnalysisReport:
    model = get_model(db, current_user, model_id)
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    metrics = list(db.scalars(statement).all())
    grouped = _metric_summary(metrics)

    f1_values = [values.get("f1", 0) for values in grouped.values()]
    avg_f1 = round(sum(f1_values) / len(f1_values), 4) if f1_values else 0
    evaluation_context = _model_evaluation_context(db, current_user, model.id, model.task_type)
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
    }
    text = await _call_llm(db, current_user, "model_analysis", prompt_vars)
    return save_ai_report(db, current_user, "model_analysis", text, summary, model_id=model_id)


async def generate_prediction_explanation(db: Session, current_user: User, prediction_job_id: int) -> AIAnalysisReport:
    job = db.get(PredictionJob, prediction_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")
    statement = select(PredictionResult).where(PredictionResult.job_id == job.id).order_by(PredictionResult.sample_index)
    results = list(db.scalars(statement).all())
    first_prediction = results[0].prediction_json if results else {}
    summary = {"job_id": job.id, "job_type": job.job_type, "first_prediction": first_prediction}

    prompt_vars = {
        "job_type": job.job_type,
        "sample_count": str(len(results)),
        "prediction_summary": _json_for_prompt(first_prediction),
    }
    text = await _call_llm(db, current_user, "prediction_explanation", prompt_vars)
    return save_ai_report(
        db, current_user, "prediction_explanation", text, summary,
        model_id=job.model_id, prediction_job_id=job.id,
    )


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
