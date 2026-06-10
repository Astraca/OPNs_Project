"""Rule-based privacy field classification for medical datasets.

Classifies dataset columns into four risk categories:
  1. direct_identifier   — must NOT be sent to AI or used in modeling
  2. quasi_identifier     — may re-identify when combined; send only in summary form
  3. sensitive_medical    — medical data; use summary statistics only
  4. normal_modeling      — safe for AI-assisted analysis
"""

import re
from typing import Any, Literal

from app.db_models.dataset import DatasetColumn


PrivacyClass = Literal[
    "direct_identifier",
    "quasi_identifier",
    "sensitive_medical",
    "normal_modeling",
]

RiskLevel = Literal["high", "medium", "low"]


# ── Detection patterns ───────────────────────────────────────────────────────

# Direct identifiers — should never be sent to external AI
DIRECT_IDENTIFIER_PATTERNS: list[re.Pattern] = [
    re.compile(pat, re.IGNORECASE)
    for pat in [
        r"\bname\b",                     # name, Name
        r"\b姓名\b",
        r"\b身份证[号碼]?\b",
        r"\bid_card\b",
        r"\b手机[号號]?\b",
        r"\bphone\b",
        r"\bmobile\b",
        r"\b电话\b",
        r"\b住院号\b",
        r"\b门诊号\b",
        r"\b病历号\b",
        r"\b病案号\b",
        r"\b医保号\b",
        r"\bpatient_id\b",
        r"\brecord_id\b",
        r"\bhospital_id\b",
        r"\bemail\b",
        r"\b邮箱\b",
        r"\baddress\b",                  # 地址
        r"\b地址\b",
        r"\bssn\b",
        r"\b社保\b",
    ]
]

# Quasi-identifier patterns — columns that may re-identify when combined
QUASI_IDENTIFIER_PATTERNS: list[re.Pattern] = [
    re.compile(pat, re.IGNORECASE)
    for pat in [
        r"\b出生日期\b",
        r"\bdate_of_birth\b",
        r"\bbirth_date\b",
        r"\b入院日期\b",
        r"\b出院日期\b",
        r"\b就诊日期\b",
        r"\badmission_date\b",
        r"\bdischarge_date\b",
        r"\bvisit_date\b",
        r"\bzip_code\b",
        r"\bpostal_code\b",
        r"\b邮编\b",
        r"\b籍贯\b",
        r"\b民族\b",
        r"\bethnicity\b",
        r"\b地区\b",
        r"\bregion\b",
        r"\bcity\b",
    ]
]

# Sensitive medical patterns — should only be sent as summaries
SENSITIVE_MEDICAL_PATTERNS: list[re.Pattern] = [
    re.compile(pat, re.IGNORECASE)
    for pat in [
        r"\b诊断\b",
        r"\bdiagnosis\b",
        r"\b病理\b",
        r"\bpathology\b",
        r"\b活检\b",
        r"\bbiopsy\b",
        r"\b医嘱\b",
        r"\b处方\b",
        r"\bprescription\b",
        r"\b用药\b",
        r"\bmedication\b",
        r"\bdrug\b",
        r"\b治疗\b",
        r"\btreatment\b",
        r"\b手术\b",
        r"\bsurgery\b",
        r"\b病程\b",
        r"\b遗传\b",
        r"\bgenetic\b",
        r"\b感染\b",
        r"\binfection\b",
    ]
]


def _matches_any(name: str, patterns: list[re.Pattern]) -> bool:
    return any(pat.search(name) for pat in patterns)


def classify_field(column: DatasetColumn, total_rows: int) -> dict[str, Any]:
    """Classify a single dataset column's privacy risk.

    Args:
        column: DatasetColumn ORM object.
        total_rows: Total sample count for unique-ratio calculation.

    Returns:
        Dict with keys: field, classification, reason, risk_level.
    """
    name = column.column_name
    # Lower-case for English pattern matching, original for Chinese
    name_lower = name.lower()

    # 1. Direct identifiers by name patterns
    if _matches_any(name, DIRECT_IDENTIFIER_PATTERNS) or _matches_any(
        name_lower, DIRECT_IDENTIFIER_PATTERNS,
    ):
        return {
            "field": name,
            "classification": "direct_identifier",
            "reason": f"字段名 '{name}' 匹配已知身份标识模式（如姓名、ID、住院号等）",
            "risk_level": "high",
        }

    # 2. Quasi-identifiers by name patterns
    if _matches_any(name, QUASI_IDENTIFIER_PATTERNS) or _matches_any(
        name_lower, QUASI_IDENTIFIER_PATTERNS,
    ):
        return {
            "field": name,
            "classification": "quasi_identifier",
            "reason": f"字段名 '{name}' 包含可能间接识别个人的信息（如日期、地址等）",
            "risk_level": "medium",
        }

    # 3. High-cardinality columns (unique ratio >= 0.99) = likely identifier
    if total_rows > 0:
        unique_ratio = column.unique_count / total_rows
        if unique_ratio >= 0.99 and column.unique_count > 1:
            return {
                "field": name,
                "classification": "quasi_identifier",
                "reason": (
                    f"字段 '{name}' 唯一值比例过高 ({unique_ratio:.2%})，"
                    "疑似唯一标识符，不建议发送给外部 AI"
                ),
                "risk_level": "high",
            }

    # 4. Sensitive medical data
    if _matches_any(name, SENSITIVE_MEDICAL_PATTERNS) or _matches_any(
        name_lower, SENSITIVE_MEDICAL_PATTERNS,
    ):
        return {
            "field": name,
            "classification": "sensitive_medical",
            "reason": f"字段名 '{name}' 包含医学敏感信息关键词",
            "risk_level": "medium",
        }

    # 5. Normal modeling field
    return {
        "field": name,
        "classification": "normal_modeling",
        "reason": "未检测到隐私风险",
        "risk_level": "low",
    }


def scan_dataset(columns: list[DatasetColumn], sample_count: int) -> dict[str, Any]:
    """Run privacy scan on all columns of a dataset.

    Returns a dict suitable for serialization and storage.
    """
    classifications = [classify_field(col, sample_count) for col in columns]

    direct_ids = [c for c in classifications if c["classification"] == "direct_identifier"]
    quasi_ids = [c for c in classifications if c["classification"] == "quasi_identifier"]
    sensitive = [c for c in classifications if c["classification"] == "sensitive_medical"]

    has_direct = len(direct_ids) > 0
    has_quasi = len(quasi_ids) > 0

    if has_direct:
        risk_summary = (
            f"检测到 {len(direct_ids)} 个疑似身份标识字段: "
            f"{', '.join(c['field'] for c in direct_ids)}。"
            "强烈建议在调用 AI 分析前将这些字段设为 ignored。"
        )
    elif has_quasi:
        risk_summary = (
            f"检测到 {len(quasi_ids)} 个可能间接识别个人的字段。"
            "建议仅发送统计摘要，不发送完整行数据。"
        )
    else:
        risk_summary = "未检测到高隐私风险字段。"

    return {
        "classifications": classifications,
        "has_direct_identifiers": has_direct,
        "has_quasi_identifiers": has_quasi,
        "sensitive_medical_count": len(sensitive),
        "risk_summary": risk_summary,
    }
