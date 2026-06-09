from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db_models.ai_report import AIAnalysisReport
from app.db_models.ml_model import ModelMetric
from app.db_models.prediction import PredictionJob, PredictionResult
from app.db_models.user import User
from app.schemas.prediction_schema import RESEARCH_DISCLAIMER
from app.services.dataset_service import get_dataset, get_missing_values_chart, get_profile
from app.services.training_service import get_model
from app.utils.igan_fields import display_target_name


def generate_dataset_analysis(db: Session, current_user: User, dataset_id: int) -> AIAnalysisReport:
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
    }
    text = "\n".join(
        [
            f"数据集包含 {dataset.sample_count} 条样本、{dataset.feature_count} 个字段。",
            f"当前目标字段为：{', '.join(map(display_target_name, dataset.target_columns)) or '暂未识别'}。",
            "缺失值较高字段：" + (", ".join(item["column_name"] for item in high_missing) if high_missing else "未发现缺失率超过 10% 的字段。"),
            "建模前建议确认 ignored 字段是否已排除，尤其是姓名、住院号、编号、日期等标识信息。",
            "若某些标签分布明显不均衡，模型评估时应重点关注 Precision、Recall 和 F1，而不只看 Accuracy。",
            RESEARCH_DISCLAIMER,
        ]
    )
    return save_ai_report(db, current_user, "dataset_analysis", text, summary, dataset_id=dataset_id)


def generate_model_analysis(db: Session, current_user: User, model_id: int) -> AIAnalysisReport:
    model = get_model(db, current_user, model_id)
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    metrics = list(db.scalars(statement).all())
    grouped: dict[str, dict[str, float]] = {}
    for metric in metrics:
        target = display_target_name(metric.target_name or "overall")
        grouped.setdefault(target, {})[metric.metric_name] = round(metric.metric_value, 4)

    f1_values = [values.get("f1", 0) for values in grouped.values()]
    avg_f1 = round(sum(f1_values) / len(f1_values), 4) if f1_values else 0
    summary = {
        "algorithm": model.algorithm,
        "target_columns": model.target_columns,
        "feature_columns": model.feature_columns,
        "metrics": grouped,
    }
    text = "\n".join(
        [
            f"模型 {model.model_name} 使用 {model.algorithm} 算法，输入特征数为 {len(model.feature_columns)}。",
            f"当前各标签平均 F1 约为 {avg_f1}，可作为模型整体分类表现的初步参考。",
            "不同标签表现差异应结合样本量、类别不平衡和缺失值情况理解。",
            "若 OPNs-SVM 相比标准 SVM 指标提升，可能说明结构特征对当前表格数据有补充表达能力。",
            "该分析不代表医学诊断能力，只用于模型验证和科研讨论。",
            RESEARCH_DISCLAIMER,
        ]
    )
    return save_ai_report(db, current_user, "model_analysis", text, summary, model_id=model_id)


def generate_prediction_explanation(db: Session, current_user: User, prediction_job_id: int) -> AIAnalysisReport:
    job = db.get(PredictionJob, prediction_job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")
    statement = select(PredictionResult).where(PredictionResult.job_id == job.id).order_by(PredictionResult.sample_index)
    results = list(db.scalars(statement).all())
    first_prediction = results[0].prediction_json if results else {}
    summary = {"job_id": job.id, "job_type": job.job_type, "first_prediction": first_prediction}
    text = "\n".join(
        [
            f"预测任务 {job.id} 类型为 {job.job_type}，共生成 {len(results)} 条预测结果。",
            "单个标签的概率仅表示模型在当前训练数据和特征处理流程下的分类置信度，不等同于临床风险概率。",
            "如多个标签概率接近，说明模型不确定性较高，应结合数据质量和模型评估结果谨慎解读。",
            "该说明不包含诊断结论、治疗建议或用药建议。",
            RESEARCH_DISCLAIMER,
        ]
    )
    return save_ai_report(
        db,
        current_user,
        "prediction_explanation",
        text,
        summary,
        model_id=job.model_id,
        prediction_job_id=job.id,
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
