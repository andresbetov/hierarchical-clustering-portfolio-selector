"""Central, immutable and validated configuration for the engine (M1).

Contract-first: field names preserve the historical attribute API so all
consumers keep working; construction is the single validated entry point
and mutation afterwards is structurally impossible.
"""

from dataclasses import dataclass

# Executable documentation of the supported allocation strategies.
WEIGHT_ALLOCATION_METHODS = (
    "equal",
    "inverse_volatility",
    "risk_parity",
    "max_sharpe",
    "min_variance",
)

# Clustering distance modes (ADR 002): signed is the methodologically
# correct default; abs preserves legacy behavior on demand.
DISTANCE_METRICS = ("signed", "abs")

_WEIGHT_SUM_TOLERANCE = 1e-9


def _require_range(name: str, value: float, low: float, high: float) -> None:
    if not (low <= value <= high):
        raise ValueError(f"{name} must be within [{low}, {high}], got {value}")


@dataclass(frozen=True)
class PortfolioConfig:
    """Immutable profile governing filtering, selection and weighting.

    Medium-risk equity defaults; construct with keyword overrides instead of
    mutating (mutation raises FrozenInstanceError by design).
    """

    # Asset filtering parameters
    minimum_sharpe_threshold: float = 0.5
    maximum_volatility_threshold: float = 0.25
    maximum_correlation_threshold: float = 0.65

    # Clustering distance metric (ADR 002): signed keeps diversifiers apart.
    distance_metric: str = "signed"

    # Portfolio selection scoring weights (must sum to 1.0)
    sharpe_weight: float = 0.45
    diversification_weight: float = 0.35
    volatility_penalty_weight: float = 0.20

    # Risk parameters
    risk_free_rate: float = 0.045
    volatility_penalty_scale: float = 0.20
    max_volatility_penalty_multiplier: float = 3.0

    # Weight allocation parameters
    weight_allocation_method: str = "risk_parity"
    maximum_single_asset_weight: float = 0.30
    minimum_single_asset_weight: float = 0.05

    # Data window
    lookback_years: int = 5

    # Annualization constant per market calendar (crypto uses 365, etc.)
    trading_days_per_year: int = 252

    def __post_init__(self) -> None:
        weight_sum = self.sharpe_weight + self.diversification_weight + self.volatility_penalty_weight
        if abs(weight_sum - 1.0) > _WEIGHT_SUM_TOLERANCE:
            raise ValueError(
                "Scoring weights must sum to 1.0 "
                f"(got {weight_sum:.12f}: sharpe={self.sharpe_weight}, "
                f"diversification={self.diversification_weight}, "
                f"volatility_penalty={self.volatility_penalty_weight})"
            )

        for weight_name in ("sharpe_weight", "diversification_weight", "volatility_penalty_weight"):
            _require_range(weight_name, getattr(self, weight_name), 0.0, 1.0)

        _require_range("risk_free_rate", self.risk_free_rate, 0.0, 1.0)

        if self.maximum_volatility_threshold <= 0:
            raise ValueError(
                f"maximum_volatility_threshold must be strictly positive, got {self.maximum_volatility_threshold}"
            )

        if self.minimum_single_asset_weight > self.maximum_single_asset_weight:
            raise ValueError(
                f"minimum_single_asset_weight ({self.minimum_single_asset_weight}) "
                f"cannot exceed maximum_single_asset_weight ({self.maximum_single_asset_weight})"
            )

        if self.lookback_years < 1:
            raise ValueError(f"lookback_years must be >= 1, got {self.lookback_years}")

        if not (1 <= self.trading_days_per_year <= 366):
            raise ValueError(
                f"trading_days_per_year must be within [1, 366], got {self.trading_days_per_year}"
            )

        if self.weight_allocation_method not in WEIGHT_ALLOCATION_METHODS:
            raise ValueError(
                f"weight_allocation_method '{self.weight_allocation_method}' is invalid; "
                f"allowed values: {list(WEIGHT_ALLOCATION_METHODS)}"
            )

        if self.distance_metric not in DISTANCE_METRICS:
            raise ValueError(
                f"distance_metric '{self.distance_metric}' is invalid; "
                f"allowed values: {list(DISTANCE_METRICS)}"
            )
