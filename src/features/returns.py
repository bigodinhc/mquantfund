"""
Cálculo de retornos em múltiplas janelas temporais.

Fornece funções para calcular retornos simples, logarítmicos e
acumulados em diferentes períodos (1d, 5d, 10d, 20d).

Uso:
    from src.features.returns import calculate_returns, add_return_features

    # Calcular retornos simples
    returns = calculate_returns(prices, periods=[1, 5, 20])

    # Adicionar features de retorno a um DataFrame
    df = add_return_features(df, price_col='close', periods=[1, 5, 10, 20])
"""

import numpy as np
import pandas as pd
from loguru import logger


def calculate_returns(
    prices: pd.Series,
    periods: list[int] | None = None,
    method: str = "simple",
) -> pd.DataFrame:
    """
    Calcula retornos para múltiplos períodos.

    Args:
        prices: Série de preços (index deve ser datetime ou ordenado)
        periods: Lista de períodos para calcular retornos (default: [1, 5, 10, 20])
        method: Método de cálculo ('simple' ou 'log')

    Returns:
        DataFrame com colunas de retornos para cada período

    Examples:
        >>> prices = pd.Series([100, 102, 101, 105, 103])
        >>> returns = calculate_returns(prices, periods=[1, 2])
        >>> returns.columns.tolist()
        ['return_1d', 'return_2d']
    """
    if periods is None:
        periods = [1, 5, 10, 20]

    result = pd.DataFrame(index=prices.index)

    for period in periods:
        col_name = f"return_{period}d"

        if method == "simple":
            result[col_name] = prices.pct_change(periods=period) * 100
        elif method == "log":
            result[col_name] = np.log(prices / prices.shift(period)) * 100
        else:
            raise ValueError(f"Método inválido: {method}. Use 'simple' ou 'log'")

    logger.debug(f"Calculados retornos para períodos: {periods}")
    return result


def calculate_cumulative_return(
    prices: pd.Series,
    window: int = 20,
) -> pd.Series:
    """
    Calcula retorno acumulado em uma janela rolling.

    Args:
        prices: Série de preços
        window: Tamanho da janela em dias

    Returns:
        Série com retorno acumulado (%)
    """
    return ((prices / prices.shift(window)) - 1) * 100


def calculate_momentum(
    prices: pd.Series,
    short_period: int = 5,
    long_period: int = 20,
) -> pd.Series:
    """
    Calcula momentum como diferença entre retornos de curto e longo prazo.

    Args:
        prices: Série de preços
        short_period: Período curto (default: 5 dias)
        long_period: Período longo (default: 20 dias)

    Returns:
        Série com momentum (diferença de retornos %)
    """
    short_return = prices.pct_change(periods=short_period) * 100
    long_return = prices.pct_change(periods=long_period) * 100
    return short_return - long_return


def add_return_features(
    df: pd.DataFrame,
    price_col: str,
    periods: list[int] | None = None,
    prefix: str = "",
    include_momentum: bool = True,
    include_cumulative: bool = True,
) -> pd.DataFrame:
    """
    Adiciona features de retorno a um DataFrame.

    Args:
        df: DataFrame com coluna de preços
        price_col: Nome da coluna de preços
        periods: Períodos para calcular retornos (default: [1, 5, 10, 20])
        prefix: Prefixo para nomes das colunas (ex: 'iron_' → 'iron_return_1d')
        include_momentum: Se True, inclui momentum (5d vs 20d)
        include_cumulative: Se True, inclui retorno acumulado 20d

    Returns:
        DataFrame com novas colunas de retorno

    Examples:
        >>> df = pd.DataFrame({'close': [100, 102, 101, 105, 103]})
        >>> df = add_return_features(df, 'close', periods=[1])
        >>> 'return_1d' in df.columns
        True
    """
    if periods is None:
        periods = [1, 5, 10, 20]

    df = df.copy()
    prices = df[price_col]

    # Retornos básicos
    returns = calculate_returns(prices, periods=periods)
    for col in returns.columns:
        new_col = f"{prefix}{col}" if prefix else col
        df[new_col] = returns[col]

    # Momentum
    if include_momentum and 5 in periods and 20 in periods:
        momentum_col = f"{prefix}momentum_5_20" if prefix else "momentum_5_20"
        df[momentum_col] = calculate_momentum(prices, short_period=5, long_period=20)

    # Retorno acumulado
    if include_cumulative:
        cum_col = f"{prefix}cumulative_return_20d" if prefix else "cumulative_return_20d"
        df[cum_col] = calculate_cumulative_return(prices, window=20)

    logger.debug(f"Adicionadas features de retorno para '{price_col}'")
    return df


def calculate_relative_return(
    prices_a: pd.Series,
    prices_b: pd.Series,
    period: int = 1,
) -> pd.Series:
    """
    Calcula retorno relativo entre dois ativos.

    Args:
        prices_a: Série de preços do ativo A
        prices_b: Série de preços do ativo B
        period: Período para calcular retorno

    Returns:
        Série com retorno_A - retorno_B (%)
    """
    return_a = prices_a.pct_change(periods=period) * 100
    return_b = prices_b.pct_change(periods=period) * 100
    return return_a - return_b


def calculate_lagged_returns(
    prices: pd.Series,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """
    Calcula retornos defasados (para features de predição).

    Args:
        prices: Série de preços
        lags: Lista de defasagens (default: [1, 2, 3, 4, 5])

    Returns:
        DataFrame com retornos defasados

    Examples:
        >>> # Para usar retorno de ontem como feature para hoje:
        >>> lagged = calculate_lagged_returns(prices, lags=[1])
        >>> # lagged['return_lag_1'] contém o retorno de D-1
    """
    if lags is None:
        lags = [1, 2, 3, 4, 5]

    result = pd.DataFrame(index=prices.index)
    daily_return = prices.pct_change() * 100

    for lag in lags:
        result[f"return_lag_{lag}"] = daily_return.shift(lag)

    return result
