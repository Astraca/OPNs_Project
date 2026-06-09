import pandas as pd

from app.ml.feature_mapper import DEFAULT_MAPPING_CONFIG, apply_mappings
from app.ml.pairing_strategy import adjacent_pairing, correlation_greedy_pairing, random_pairing


class OPNsTransformer:
    """Ordered-Pair Norms feature transformer.

    Pairs original features and maps each pair to structural features
    (sum, diff, abs_diff, product, square_sum), producing an expanded
    feature set for SVM/SVR training.
    """

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
        return apply_mappings(dataframe, self.pairs_, self.mapping_config)

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)

    def _to_dataframe(self, X) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X, columns=self.feature_names_ or None)
