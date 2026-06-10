from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models.ml_model import MLModel, ModelMetric
from app.db_models.report import Report
from app.db_models.user import User
from app.schemas.prediction_schema import RESEARCH_DISCLAIMER
from app.services.training_service import get_model
from app.utils.igan_fields import display_target_name


def generate_experiment_report(
    db: Session,
    current_user: User,
    model_id: int,
    title: str | None = None,
) -> Report:
    """Generate a comprehensive experiment report for a trained model."""
    model = get_model(db, current_user, model_id)

    # Gather metrics
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    metrics = list(db.scalars(statement).all())

    # Build report sections
    lines: list[str] = []
    lines.append(f"# 实验报告：{title or model.model_name}")
    lines.append("")
    lines.append("## 1. 模型信息")
    lines.append("")
    lines.append(f"- 模型名称：{model.model_name}")
    lines.append(f"- 算法：{model.algorithm}")
    lines.append(f"- 任务类型：{model.task_type}")
    lines.append(f"- 目标字段：{', '.join(display_target_name(t) for t in model.target_columns)}")
    lines.append(f"- 特征数量：{len(model.feature_columns)}")
    lines.append(f"- OPNs 启用：{'是' if model.opns_enabled else '否'}")
    if model.pairing_method:
        lines.append(f"- 配对方式：{model.pairing_method}")
    lines.append("")

    lines.append("## 2. 输入特征")
    lines.append("")
    for idx, feature in enumerate(model.feature_columns, 1):
        lines.append(f"{idx}. {feature}")
    lines.append("")

    lines.append("## 3. 模型指标")
    lines.append("")
    if model.task_type == "regression":
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        for metric in metrics:
            lines.append(f"| {metric.metric_name.upper()} | {metric.metric_value:.4f} |")
    else:
        lines.append("| 标签 | Accuracy | Precision | Recall | F1 |")
        lines.append("|------|----------|-----------|--------|-----|")
        grouped: dict[str, dict[str, float]] = {}
        for metric in metrics:
            target = display_target_name(metric.target_name or "overall")
            grouped.setdefault(target, {})[metric.metric_name] = round(metric.metric_value, 4)
        for target, values in grouped.items():
            lines.append(
                f"| {target} | {values.get('accuracy', 0):.4f} | "
                f"{values.get('precision', 0):.4f} | {values.get('recall', 0):.4f} | "
                f"{values.get('f1', 0):.4f} |",
            )
    lines.append("")

    lines.append("## 4. 超参数")
    lines.append("")
    for key, value in model.hyperparameters.items():
        lines.append(f"- {key}：{value}")
    lines.append("")

    lines.append("## 5. 科研声明")
    lines.append("")
    lines.append(RESEARCH_DISCLAIMER)

    content = "\n".join(lines)

    report = Report(
        user_id=current_user.id,
        model_id=model.id,
        dataset_id=model.dataset_id,
        title=title or f"{model.model_name} 实验报告",
        content=content,
        report_type="experiment",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(db: Session, current_user: User) -> list[Report]:
    statement = (
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_report(db: Session, current_user: User, report_id: int) -> Report:
    from fastapi import HTTPException, status

    report = db.get(Report, report_id)
    if report is None or report.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


def delete_report(db: Session, current_user: User, report_id: int) -> None:
    report = get_report(db, current_user, report_id)
    db.delete(report)
    db.commit()
