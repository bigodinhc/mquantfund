"""
Cálculo de métricas de volatilidade.

Fornece funções para calcular ATR (Average True Range), desvio padrão
rolling e outras métricas de volatilidade.

Uso:
    from src.features.volatility import calculate_atr, calculate_rolling_std

    # Calcular ATR
    atr = calculate_atr(df, period=14)

    # Calcular desvio padrão rolling de retornos
    std = calculate_rolling_std(returns, windows=[5, 10, 20])
"""

import numpy as np
import pandas as pd
from loguru import logger


def calculate_true_range(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> pd.Series:
    """
    Calcula True Range para cada dia.

    True Range = max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close)
    )

    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        close: Série de preços de fechamento

    Returns:
        Série com True Range
    """
    prev_close = close.shift(1)

    tr1 = high - low  # Range do dia
    tr2 = abs(high - prev_close)  # Gap de alta
    tr3 = abs(low - prev_close)  # Gap de baixa

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range


def calculate_atr(
    df: pd.DataFrame,
    period: int = 14,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """
    Calcula Average True Range (ATR).

    ATR é a média móvel do True Range, usada para:
    - Position sizing (stop = 2 * ATR)
    - Filtro de volatilidade
    - Normalização de movimentos

    Args:
        df: DataFrame com colunas high, low, close
        period: Período para média (default: 14 dias)
        high_col: Nome da coluna de máxima
        low_col: Nome da coluna de mínima
        close_col: Nome da coluna de fechamento

    Returns:
        Série com ATR

    Examples:
        >>> atr = calculate_atr(df, period=14)
        >>> stop_loss = 2 * atr  # Stop de 2x ATR
    """
    true_range = calculate_true_range(df[high_col], df[low_col], df[close_col])
    atr = true_range.rolling(window=period).mean()

    logger.debug(f"Calculado ATR({period})")
    return atr


def calculate_atr_percent(
    df: pd.DataFrame,
    period: int = 14,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.Series:
    """
    Calcula ATR como percentual do preço (normalizado).

    Útil para comparar volatilidade entre ativos com preços diferentes.

    Args:
        df: DataFrame com colunas high, low, close
        period: Período para média (default: 14 dias)

    Returns:
        Série com ATR em percentual (%)
    """
    atr = calculate_atr(df, period, high_col, low_col, close_col)
    return (atr / df[close_col]) * 100


def calculate_rolling_std(
    returns: pd.Series,
    windows: list[int] | None = None,
) -> pd.DataFrame:
    """
    Calcula desvio padrão rolling de retornos em múltiplas janelas.

    Args:
        returns: Série de retornos (%)
        windows: Lista de janelas em dias (default: [5, 10, 20])

    Returns:
        DataFrame com colunas de volatilidade para cada janela

    Examples:
        >>> returns = df['close'].pct_change() * 100
        >>> vol = calculate_rolling_std(returns, windows=[5, 20])
        >>> vol.columns.tolist()
        ['volatility_5d', 'volatility_20d']
    """
    if windows is None:
        windows = [5, 10, 20]

    result = pd.DataFrame(index=returns.index)

    for window in windows:
        result[f"volatility_{window}d"] = returns.rolling(window=window).std()

    logger.debug(f"Calculada volatilidade rolling para janelas: {windows}")
    return result


def calculate_annualized_volatility(
    returns: pd.Series,
    window: int = 20,
    trading_days: int = 252,
) -> pd.Series:
    """
    Calcula volatilidade anualizada.

    Args:
        returns: Série de retornos diários (%)
        window: Janela para cálculo (default: 20 dias)
        trading_days: Dias de trading por ano (default: 252)

    Returns:
        Série com volatilidade anualizada (%)
    """
    daily_std = returns.rolling(window=window).std()
    return daily_std * np.sqrt(trading_days)


def calculate_volatility_ratio(
    returns: pd.Series,
    short_window: int = 5,
    long_window: int = 20,
) -> pd.Series:
    """
    Calcula razão de volatilidade curto/longo prazo.

    Útil para detectar mudanças de regime:
    - Ratio > 1: Volatilidade aumentando (stress)
    - Ratio < 1: Volatilidade diminuindo (calma)

    Args:
        returns: Série de retornos
        short_window: Janela curta (default: 5 dias)
        long_window: Janela longa (default: 20 dias)

    Returns:
        Série com razão de volatilidade
    """
    short_vol = returns.rolling(window=short_window).std()
    long_vol = returns.rolling(window=long_window).std()
    return short_vol / long_vol


def add_volatility_features(
    df: pd.DataFrame,
    close_col: str = "close",
    high_col: str | None = None,
    low_col: str | None = None,
    prefix: str = "",
    windows: list[int] | None = None,
    include_atr: bool = True,
    include_ratio: bool = True,
) -> pd.DataFrame:
    """
    Adiciona features de volatilidade a um DataFrame.

    Args:
        df: DataFrame com dados de preços
        close_col: Nome da coluna de fechamento
        high_col: Nome da coluna de máxima (para ATR)
        low_col: Nome da coluna de mínima (para ATR)
        prefix: Prefixo para nomes das colunas
        windows: Janelas para volatilidade rolling (default: [5, 10, 20])
        include_atr: Se True e high/low disponíveis, inclui ATR
        include_ratio: Se True, inclui volatility ratio (5d/20d)

    Returns:
        DataFrame com novas colunas de volatilidade
    """
    if windows is None:
        windows = [5, 10, 20]

    df = df.copy()

    # Calcula retornos para volatilidade
    returns = df[close_col].pct_change() * 100

    # Volatilidade rolling
    vol = calculate_rolling_std(returns, windows=windows)
    for col in vol.columns:
        new_col = f"{prefix}{col}" if prefix else col
        df[new_col] = vol[col]

    # ATR (se high/low disponíveis)
    if include_atr and high_col and low_col:
        if high_col in df.columns and low_col in df.columns:
            for period in [14, 20]:
                atr_col = f"{prefix}atr_{period}" if prefix else f"atr_{period}"
                df[atr_col] = calculate_atr(
                    df, period=period,
                    high_col=high_col, low_col=low_col, close_col=close_col
                )
                # ATR percentual
                atr_pct_col = f"{prefix}atr_pct_{period}" if prefix else f"atr_pct_{period}"
                df[atr_pct_col] = (df[atr_col] / df[close_col]) * 100

    # Volatility ratio
    if include_ratio and 5 in windows and 20 in windows:
        ratio_col = f"{prefix}vol_ratio_5_20" if prefix else "vol_ratio_5_20"
        df[ratio_col] = calculate_volatility_ratio(returns, short_window=5, long_window=20)

    logger.debug(f"Adicionadas features de volatilidade para '{close_col}'")
    return df


def calculate_parkinson_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int = 20,
) -> pd.Series:
    """
    Calcula volatilidade de Parkinson (baseada em high-low).

    Mais eficiente que volatilidade baseada em close-to-close.

    Args:
        high: Série de preços máximos
        low: Série de preços mínimos
        window: Janela para cálculo

    Returns:
        Série com volatilidade de Parkinson (%)
    """
    log_hl = np.log(high / low)
    factor = 1 / (4 * np.log(2))
    variance = factor * (log_hl ** 2)
    return np.sqrt(variance.rolling(window=window).mean()) * 100 * np.sqrt(252)
