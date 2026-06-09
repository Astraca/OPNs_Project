import random

import numpy as np
import pandas as pd


def adjacent_pairing(feature_names: list[str]) -> list[tuple[str, str]]:
    return [(feature_names[index], feature_names[index + 1]) for index in range(0, len(feature_names) - 1, 2)]


def random_pairing(feature_names: list[str], random_state: int | None = None) -> list[tuple[str, str]]:
    shuffled = list(feature_names)
    random.Random(random_state).shuffle(shuffled)
    return adjacent_pairing(shuffled)


def correlation_greedy_pairing(
    X: pd.DataFrame,
    y: pd.Series | pd.DataFrame | np.ndarray,
    feature_names: list[str],
) -> list[tuple[str, str]]:
    numeric = X[feature_names].apply(pd.to_numeric, errors="coerce")
    if isinstance(y, pd.DataFrame):
        encoded_target = y.apply(lambda column: pd.factorize(column)[0]).mean(axis=1)
    elif isinstance(y, pd.Series):
        encoded_target = pd.Series(pd.factorize(y)[0], index=X.index)
    else:
        encoded_target = pd.Series(np.asarray(y).ravel(), index=X.index)

    relevance = numeric.corrwith(encoded_target).abs().fillna(0).sort_values(ascending=False)
    ordered = [feature for feature in relevance.index if feature in feature_names]
    used: set[str] = set()
    pairs: list[tuple[str, str]] = []

    for feature in ordered:
        if feature in used:
            continue
        remaining = [candidate for candidate in ordered if candidate not in used and candidate != feature]
        if not remaining:
            break
        correlations = numeric[remaining].corrwith(numeric[feature]).abs().fillna(0)
        partner = correlations.sort_values().index[0]
        pairs.append((feature, str(partner)))
        used.update({feature, str(partner)})

    return pairs
