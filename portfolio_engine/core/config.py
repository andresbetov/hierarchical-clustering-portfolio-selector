class PortfolioConfig:
    """Central configuration used across filtering, selection and weighting.

    Values are tuned as defaults for a medium-risk equity portfolio and can be
    overridden from scripts/tests without changing engine code.
    """

    def __init__(self):
        # Asset filtering parameters
        self.minimum_sharpe_threshold = 0.5
        self.maximum_volatility_threshold = 0.25
        self.maximum_correlation_threshold = 0.65

        # Portfolio selection scoring weights (must sum to 1.0)
        self.sharpe_weight = 0.45
        self.diversification_weight = 0.35
        self.volatility_penalty_weight = 0.20

        # Risk parameters
        self.risk_free_rate = 0.045
        self.volatility_penalty_scale = 0.20
        self.max_volatility_penalty_multiplier = 3.0

        # Weight allocation parameters
        self.weight_allocation_method = "risk_parity"
        self.target_portfolio_volatility = 0.15
        self.maximum_single_asset_weight = 0.30
        self.minimum_single_asset_weight = 0.05

