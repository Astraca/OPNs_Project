from collections.abc import Iterable


MESTC_TARGETS = ["out-M", "out-E", "out-S", "out-T", "out-C"]
LEGACY_MESTC_TARGETS = ["M", "E", "S", "T", "C"]
IDENTIFIER_COLUMNS = {"编号", "住院号", "姓名", "出生年月日", "肾穿年月日"}

# Columns that look like identifiers in any dataset
GENERIC_IDENTIFIER_PATTERNS = [
    "id", "index", "uuid", "guid", "row", "row_id", "sample_id",
    "编号", "序号", "编号", "住院号", "病案号",
    "name", "姓名", "名字",
    "date", "日期", "时间", "出生", "肾穿",
]


def get_output_columns(columns: Iterable[str]) -> list[str]:
    """Auto-detect target columns by 'out-' prefix (IgAN convention)."""
    return [column for column in columns if str(column).startswith("out-")]


def get_mestc_target_columns(columns: Iterable[str]) -> list[str]:
    """Return M/E/S/T/C target columns from the given column list.

    First tries 'out-' prefixed names, then legacy unprefixed names.
    Returns empty list if none are found (non-IgAN data).
    """
    column_list = [str(column) for column in columns]
    output_targets = [target for target in MESTC_TARGETS if target in column_list]
    if output_targets:
        return output_targets
    return [target for target in LEGACY_MESTC_TARGETS if target in column_list]


def is_igans_dataset(columns: Iterable[str]) -> bool:
    """Check if this dataset appears to be an IgAN dataset."""
    column_set = {str(c) for c in columns}
    return bool(
        column_set & set(MESTC_TARGETS) or column_set & set(LEGACY_MESTC_TARGETS),
    )


def get_default_feature_columns(columns: Iterable[str], target_columns: Iterable[str]) -> list[str]:
    """Return columns that should be used as features (exclude targets and identifiers)."""
    targets = set(target_columns)
    return [
        str(column)
        for column in columns
        if str(column) not in targets
        and not str(column).startswith("out-")
        and str(column) not in IDENTIFIER_COLUMNS
        and not _is_likely_identifier(str(column))
    ]


def infer_column_role(column: str, target_columns: Iterable[str]) -> str:
    """Infer the role of a column: target, feature, or ignored."""
    col_lower = column.lower()
    if column in set(target_columns) or column.startswith("out-"):
        return "target"
    if column in IDENTIFIER_COLUMNS:
        return "ignored"
    if _is_likely_identifier(column):
        return "ignored"
    if col_lower in ("target", "label", "y", "class", "category", "outcome"):
        return "target"
    return "feature"


def suggest_target_columns(columns: Iterable[str], task_type: str) -> list[str]:
    """Suggest target columns for non-IgAN datasets based on column names.

    For classification/multi_output: look for columns named 'target', 'label', etc.
    For regression: look for continuous-looking names like 'score', 'value', 'rate'.
    Returns empty list if no candidates found.
    """
    candidates = []
    col_list = [str(c) for c in columns]
    for col in col_list:
        col_lower = col.lower().strip()
        # Skip identifier-like columns
        if _is_likely_identifier(col):
            continue
        # Common target indicator names
        if col_lower in ("target", "label", "y", "class", "category", "outcome",
                          "result", "diagnosis", "disease", "status", "group"):
            candidates.append(col)
    return candidates


def _is_likely_identifier(column: str) -> bool:
    """Check if a column name looks like an identifier."""
    col_lower = column.lower().strip()
    for pattern in GENERIC_IDENTIFIER_PATTERNS:
        if pattern in col_lower:
            return True
    # Column names that are just numbers (like col_0 from headerless files)
    if col_lower.startswith("col_") and col_lower[4:].isdigit():
        return False  # These are auto-generated, not real identifiers
    return False


def strip_io_prefix(column: str) -> str:
    if column.startswith("in-") or column.startswith("out-"):
        return column[3:]
    return column


def display_target_name(target: str) -> str:
    return target.removeprefix("out-")


def format_prediction_label(target: str, value: object) -> str:
    text = str(value)
    display = display_target_name(target)
    if target in MESTC_TARGETS or target in LEGACY_MESTC_TARGETS:
        return f"{display}{text}" if not text.startswith(display) else text
    return text
