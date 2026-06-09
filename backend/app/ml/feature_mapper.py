"""Structural feature mapping functions for OPNs feature construction.

Each function takes a pair of numeric Series and returns a single
Series representing a structural feature.
"""

import numpy as np
import pandas as pd


DEFAULT_MAPPING_CONFIG = {
    "sum": True,
    "diff": True,
    "abs_diff": True,
    "product": True,
    "square_sum": True,
}

MAPPING_LABELS: dict[str, str] = {
    "sum": "__plus__",
    "diff": "__minus__",
    "abs_diff": "__absdiff__",
    "product": "__mul__",
    "square_sum": "__squaresum__",
}


def map_sum(left: pd.Series, right: pd.Series) -> pd.Series:
    return left + right


def map_diff(left: pd.Series, right: pd.Series) -> pd.Series:
    return left - right


def map_abs_diff(left: pd.Series, right: pd.Series) -> pd.Series:
    return (left - right).abs()


def map_product(left: pd.Series, right: pd.Series) -> pd.Series:
    return left * right


def map_square_sum(left: pd.Series, right: pd.Series) -> pd.Series:
    return left.pow(2) + right.pow(2)


_MAPPER_REGISTRY = {
    "sum": map_sum,
    "diff": map_diff,
    "abs_diff": map_abs_diff,
    "product": map_product,
    "square_sum": map_square_sum,
}


def apply_mappings(
    dataframe: pd.DataFrame,
    pairs: list[tuple[str, str]],
    mapping_config: dict | None = None,
) -> pd.DataFrame:
    """Apply configured mappings to each pair and return a DataFrame
    of structural features.

    Args:
        dataframe: Input dataframe with numeric feature columns.
        pairs: List of (left_col, right_col) tuples.
        mapping_config: Dict of mapping_name → enabled (default: all on).

    Returns:
        DataFrame with columns like "left__plus__right".
    """
    config = {**DEFAULT_MAPPING_CONFIG, **(mapping_config or {})}
    features: dict[str, pd.Series] = {}

    for left, right in pairs:
        left_vals = pd.to_numeric(dataframe[left], errors="coerce").fillna(0)
        right_vals = pd.to_numeric(dataframe[right], errors="coerce").fillna(0)

        for mapping_name, mapper_fn in _MAPPER_REGISTRY.items():
            if config.get(mapping_name, True):
                label = MAPPING_LABELS[mapping_name]
                features[f"{left}{label}{right}"] = mapper_fn(left_vals, right_vals)

    if not features:
        return pd.DataFrame(index=dataframe.index)
    return pd.DataFrame(features, index=dataframe.index)
