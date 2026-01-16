"""
Feature Engineering para QuantFund Trading System.

Módulos:
    - returns: Cálculo de retornos em múltiplas janelas
    - volatility: ATR, desvio padrão rolling
    - zscore: Z-Score para normalização de retornos
    - alignment: Alinhamento temporal entre mercados

Uso:
    from src.features import (
        calculate_returns,
        add_return_features,
        calculate_atr,
        add_volatility_features,
        calculate_zscore,
        add_zscore_features,
        create_analysis_dataset,
    )
"""

# Returns
from src.features.returns import (
    calculate_returns,
    calculate_cumulative_return,
    calculate_momentum,
    add_return_features,
    calculate_relative_return,
    calculate_lagged_returns,
)

# Volatility
from src.features.volatility import (
    calculate_true_range,
    calculate_atr,
    calculate_atr_percent,
    calculate_rolling_std,
    calculate_annualized_volatility,
    calculate_volatility_ratio,
    add_volatility_features,
    calculate_parkinson_volatility,
)

# Z-Score
from src.features.zscore import (
    calculate_zscore,
    calculate_static_zscore,
    calculate_zscore_threshold,
    add_zscore_features,
    calculate_normalized_return,
    is_extreme_move,
    calculate_percentile_rank,
)

# Alignment
from src.features.alignment import (
    align_by_date,
    create_date_range,
    forward_fill_gaps,
    filter_trading_days,
    create_analysis_dataset,
    add_lagged_features,
    calculate_lead_lag_correlation,
    validate_alignment,
)

__all__ = [
    # Returns
    "calculate_returns",
    "calculate_cumulative_return",
    "calculate_momentum",
    "add_return_features",
    "calculate_relative_return",
    "calculate_lagged_returns",
    # Volatility
    "calculate_true_range",
    "calculate_atr",
    "calculate_atr_percent",
    "calculate_rolling_std",
    "calculate_annualized_volatility",
    "calculate_volatility_ratio",
    "add_volatility_features",
    "calculate_parkinson_volatility",
    # Z-Score
    "calculate_zscore",
    "calculate_static_zscore",
    "calculate_zscore_threshold",
    "add_zscore_features",
    "calculate_normalized_return",
    "is_extreme_move",
    "calculate_percentile_rank",
    # Alignment
    "align_by_date",
    "create_date_range",
    "forward_fill_gaps",
    "filter_trading_days",
    "create_analysis_dataset",
    "add_lagged_features",
    "calculate_lead_lag_correlation",
    "validate_alignment",
]
