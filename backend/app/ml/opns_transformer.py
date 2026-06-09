import pandas as pd

from app.ml.pairing_strategy import adjacent_pairing, correlation_greedy_pairing, random_pairing


DEFAULT_MAPPING_CONFIG = {
    "sum": True,
    "diff": True,
    "abs_diff": True,
    "product": True,
    "square_sum": True,
}


class OPNsTransformer:
    def __init__(
        self,
        pairing_method: str = "adjacent",
        mapping_config: dict | None = None,
        random_state: int | None = None,
    ):
        self.pairing_method = pairing_method
        self.mapping_config = {**DEFAULT_MAPPING_CONFIG, **(mapping_config or {})}
        self.random_state = random_state
        self.feature_names_: list[str] = []
        self.pairs_: list[tuple[str, str]] = []

    def fit(self, X, y=None):
        dataframe = self._to_dataframe(X)
        self.feature_names_ = list(dataframe.columns)
        if self.pairing_method == "adjacent":
            self.pairs_ = adjacent_pairing(self.feature_names_)
        elif self.pairing_method == "random":
            self.pairs_ = random_pairing(self.feature_names_, self.random_state)
        elif self.pairing_method == "correlation_greedy":
            self.pairs_ = correlation_greedy_pairing(dataframe, y, self.feature_names_)
        else:
            raise ValueError(f"Unsupported pairing method: {self.pairing_method}")
        return self

    def transform(self, X):
        dataframe = self._to_dataframe(X)
        features: dict[str, pd.Series] = {}
        for left, right in self.pairs_:
            left_values = pd.to_numeric(dataframe[left], errors="coerce").fillna(0)
            right_values = pd.to_numeric(dataframe[right], errors="coerce").fillna(0)
            if self.mapping_config.get("sum", True):
                features[f"{left}__plus__{right}"] = left_values + right_values
            if self.mapping_config.get("diff", True):
                features[f"{left}__minus__{right}"] = left_values - right_values
            if self.mapping_config.get("abs_diff", True):
                features[f"{left}__absdiff__{right}"] = (left_values - right_values).abs()
            if self.mapping_config.get("product", True):
                features[f"{left}__mul__{right}"] = left_values * right_values
            if self.mapping_config.get("square_sum", True):
                features[f"{left}__squaresum__{right}"] = left_values.pow(2) + right_values.pow(2)

        if not features:
            return pd.DataFrame(index=dataframe.index)
        return pd.DataFrame(features, index=dataframe.index)

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)

    def _to_dataframe(self, X) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X, columns=self.feature_names_ or None)
