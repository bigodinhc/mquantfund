"""
Cálculo de Z-Score para normalização de retornos.

O Z-Score mede quantos desvios padrão um valor está da média,
permitindo comparar movimentos de diferentes magnitudes.

Uso:
    from src.features.zscore import calculate_zscore, add_zscore_features

    # Calcular Z-Score de retornos
    zscore = calculate_zscore(returns, window=20)

    # Z-Score > 1.5 → movimento significativo (entrada LONG)
    # Z-Score < -1.5 → movimento significativo (entrada SHORT)
"""

import numpy as np
import pandas as pd
from loguru import logger


def calculate_zscore(
    values: pd.Series,
    window: int = 20,
    min_periods: int | None = None,
) -> pd.Series:
    """
    Calcula Z-Score rolling de uma série.

    Z-Score = (valor - média) / desvio_padrão

    Args:
        values: Série de valores (ex: retornos)
        window: Janela para cálculo de média e std (default: 20)
        min_periods: Períodos mínimos para cálculo (default: window // 2)

    Returns:
        Série com Z-Score

    Examples:
        >>> returns = pd.Series([0.5, -0.3, 1.2, -0.8, 2.5, -1.5])
        >>> zscore = calculate_zscore(returns, window=5)
        >>> # zscore > 1.5 indica movimento forte para cima
    """
    if min_periods is None:
        min_periods = max(window // 2, 2)

    rolling_mean = values.rolling(window=window, min_periods=min_periods).mean()
    rolling_std = values.rolling(window=window, min_periods=min_periods).std()

    # Evita divisão por zero
    rolling_std = rolling_std.replace(0, np.nan)

    zscore = (values - rolling_mean) / rolling_std

    logger.debug(f"Calculado Z-Score rolling com janela={window}")
    return zscore


def calculate_static_zscore(
    values: pd.Series,
    lookback: int | None = None,
) -> pd.Series:
    """
    Calcula Z-Score usando média e std de todo o período (ou lookback).

    Útil para backtesting onde se quer evitar look-ahead bias.

    Args:
        values: Série de valores
        lookback: Se especificado, usa apenas os últimos N períodos
                  para calcular média/std (default: todo o histórico)

    Returns:
        Série com Z-Score
    """
    if lookback:
        mean = values.rolling(window=lookback, min_periods=1).mean()
        std = values.rolling(window=lookback, min_periods=1).std()
    else:
        mean = values.expanding().mean()
        std = values.expanding().std()

    std = std.replace(0, np.nan)
    return (values - mean) / std


def calculate_zscore_threshold(
    values: pd.Series,
    window: int = 20,
    threshold: float = 1.5,
) -> pd.Series:
    """
    Retorna sinal baseado em Z-Score e threshold.

    Args:
        values: Série de valores
        window: Janela para Z-Score
        threshold: Limite para gerar sinal (default: 1.5)

    Returns:
        Série com sinais:
        - 1 quando Z-Score > threshold (sinal LONG)
        - -1 quando Z-Score < -threshold (sinal SHORT)
        - 0 caso contrário

    Examples:
        >>> # Na estratégia principal:
        >>> signal = calculate_zscore_threshold(iron_return, window=20, threshold=1.5)
        >>> # signal == 1 → considerar LONG
        >>> # signal == -1 → considerar SHORT
    """
    zscore = calculate_zscore(values, window=window)

    signal = pd.Series(0, index=values.index)
    signal[zscore > threshold] = 1
    signal[zscore < -threshold] = -1

    return signal


def add_zscore_features(
    df: pd.DataFrame,
    value_col: str,
    windows: list[int] | None = None,
    prefix: str = "",
    include_signal: bool = True,
    threshold: float = 1.5,
) -> pd.DataFrame:
    """
    Adiciona features de Z-Score a um DataFrame.

    Args:
        df: DataFrame com coluna de valores
        value_col: Nome da coluna para calcular Z-Score (ex: 'return_1d')
        windows: Janelas para Z-Score (default: [10, 20])
        prefix: Prefixo para nomes das colunas
        include_signal: Se True, inclui sinal baseado em threshold
        threshold: Limite para sinal (default: 1.5)

    Returns:
        DataFrame com novas colunas de Z-Score

    Examples:
        >>> df = add_zscore_features(df, 'iron_return_1d', windows=[20])
        >>> df['iron_return_1d_zscore_20'] contém o Z-Score
        >>> df['iron_return_1d_zscore_signal_20'] contém o sinal
    """
    if windows is None:
        windows = [10, 20]

    df = df.copy()
    values = df[value_col]

    for window in windows:
        zscore = calculate_zscore(values, window=window)

        zscore_col = f"{prefix}{value_col}_zscore_{window}" if prefix else f"{value_col}_zscore_{window}"
        df[zscore_col] = zscore

        if include_signal:
            signal_col = f"{prefix}{value_col}_zscore_signal_{window}" if prefix else f"{value_col}_zscore_signal_{window}"
            df[signal_col] = calculate_zscore_threshold(values, window=window, threshold=threshold)

    logger.debug(f"Adicionadas features de Z-Score para '{value_col}'")
    return df


def calculate_normalized_return(
    returns: pd.Series,
    window: int = 20,
) -> pd.Series:
    """
    Calcula retorno normalizado pela volatilidade (tipo Sharpe instantâneo).

    Args:
        returns: Série de retornos (%)
        window: Janela para volatilidade (default: 20)

    Returns:
        Série com retornos normalizados
    """
    rolling_std = returns.rolling(window=window).std()
    rolling_std = rolling_std.replace(0, np.nan)
    return returns / rolling_std


def is_extreme_move(
    values: pd.Series,
    window: int = 20,
    threshold: float = 2.0,
) -> pd.Series:
    """
    Identifica movimentos extremos (Z-Score > threshold).

    Útil para:
    - Filtrar ruído (ignorar sinais fracos)
    - Detectar breakouts/crashes
    - Ativar alertas

    Args:
        values: Série de valores
        window: Janela para Z-Score
        threshold: Limite para considerar extremo

    Returns:
        Série booleana (True = movimento extremo)
    """
    zscore = calculate_zscore(values, window=window)
    return abs(zscore) > threshold


def calculate_percentile_rank(
    values: pd.Series,
    window: int = 252,
) -> pd.Series:
    """
    Calcula rank percentil rolling de um valor.

    Alternativa ao Z-Score que não assume normalidade.

    Args:
        values: Série de valores
        window: Janela para ranking (default: 252 = 1 ano)

    Returns:
        Série com rank percentil (0-100)

    Examples:
        >>> rank = calculate_percentile_rank(returns, window=252)
        >>> # rank > 95 → top 5% mais alto no último ano
    """
    def percentile_rank(x):
        if len(x) < 2:
            return np.nan
        return (x.rank().iloc[-1] - 1) / (len(x) - 1) * 100

    return values.rolling(window=window).apply(percentile_rank, raw=False)
