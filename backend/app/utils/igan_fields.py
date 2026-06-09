from collections.abc import Iterable


MESTC_TARGETS = ["out-M", "out-E", "out-S", "out-T", "out-C"]
LEGACY_MESTC_TARGETS = ["M", "E", "S", "T", "C"]
IDENTIFIER_COLUMNS = {"编号", "住院号", "姓名", "出生年月日", "肾穿年月日"}


def get_output_columns(columns: Iterable[str]) -> list[str]:
    return [column for column in columns if str(column).startswith("out-")]


def get_mestc_target_columns(columns: Iterable[str]) -> list[str]:
    column_list = [str(column) for column in columns]
    output_targets = [target for target in MESTC_TARGETS if target in column_list]
    if output_targets:
        return output_targets
    return [target for target in LEGACY_MESTC_TARGETS if target in column_list]


def get_default_feature_columns(columns: Iterable[str], target_columns: Iterable[str]) -> list[str]:
    targets = set(target_columns)
    return [
        str(column)
        for column in columns
        if str(column) not in targets
        and not str(column).startswith("out-")
        and str(column) not in IDENTIFIER_COLUMNS
    ]


def infer_column_role(column: str, target_columns: Iterable[str]) -> str:
    if column in set(target_columns) or column.startswith("out-"):
        return "target"
    if column in IDENTIFIER_COLUMNS:
        return "ignored"
    return "feature"


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
