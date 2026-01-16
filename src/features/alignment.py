"""
Alinhamento temporal de séries de diferentes mercados.

Lida com diferenças de calendário entre SGX (Cingapura) e B3 (Brasil),
implementando forward fill para gaps e filtragem por dias de trading.

Horários de mercado (BRT):
- SGX T-Session:   20:25-09:00
- SGX T+1 Session: 09:00-17:45
- B3 (Brasil):     10:00-17:55

Janela crítica: Settlement do minério às 09:00 BRT, VALE3 abre às 10:00 BRT
→ Minério D0 está disponível 1h antes de VALE3 abrir

Uso:
    from src.features.alignment import align_datasets, create_analysis_dataset
"""

import pandas as pd
import numpy as np
from loguru import logger
from typing import Literal


def align_by_date(
    *dataframes: pd.DataFrame,
    date_col: str = "date",
    method: Literal["inner", "outer", "ffill"] = "ffill",
    reference_df: int = 0,
) -> pd.DataFrame:
    """
    Alinha múltiplos DataFrames por data.

    Args:
        *dataframes: DataFrames para alinhar (cada um com coluna de data)
        date_col: Nome da coluna de data
        method: Método de alinhamento:
            - 'inner': Apenas datas presentes em todos
            - 'outer': Todas as datas (com NaN onde faltam dados)
            - 'ffill': Forward fill para preencher gaps
        reference_df: Índice do DataFrame de referência para filtrar datas
                      (usado após ffill para filtrar dias de trading)

    Returns:
        DataFrame combinado e alinhado
    """
    if len(dataframes) == 0:
        raise ValueError("Pelo menos um DataFrame é necessário")

    # Prepara cada DataFrame
    dfs = []
    for i, df in enumerate(dataframes):
        df = df.copy()
        if date_col in df.columns:
            df = df.set_index(date_col)
        dfs.append(df)

    # Combina os DataFrames
    if method == "inner":
        combined = pd.concat(dfs, axis=1, join="inner")
    elif method == "outer":
        combined = pd.concat(dfs, axis=1, join="outer")
    elif method == "ffill":
        # Primeiro combina com outer join
        combined = pd.concat(dfs, axis=1, join="outer")
        # Aplica forward fill
        combined = combined.ffill()
        # Filtra apenas datas onde o DataFrame de referência tem dados
        if 0 <= reference_df < len(dfs):
            ref_dates = dfs[reference_df].dropna(how="all").index
            combined = combined.loc[combined.index.isin(ref_dates)]
    else:
        raise ValueError(f"Método inválido: {method}")

    logger.debug(f"Alinhados {len(dataframes)} DataFrames com método '{method}'")
    return combined


def create_date_range(
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    freq: str = "D",
) -> pd.DatetimeIndex:
    """
    Cria range de datas para reindexação.

    Args:
        start: Data inicial
        end: Data final
        freq: Frequência ('D' para diário)

    Returns:
        DatetimeIndex com todas as datas no range
    """
    return pd.date_range(start=start, end=end, freq=freq)


def forward_fill_gaps(
    df: pd.DataFrame,
    date_index: pd.DatetimeIndex | None = None,
    max_gap: int = 5,
) -> pd.DataFrame:
    """
    Preenche gaps com forward fill, limitando tamanho do gap.

    Args:
        df: DataFrame com index de datas
        date_index: Índice de datas para reindexar (opcional)
        max_gap: Máximo de dias para preencher (default: 5)
                 Gaps maiores permanecem como NaN

    Returns:
        DataFrame com gaps preenchidos
    """
    df = df.copy()

    if date_index is not None:
        df = df.reindex(date_index)

    df = df.ffill(limit=max_gap)

    return df


def filter_trading_days(
    df: pd.DataFrame,
    trading_dates: pd.DatetimeIndex | pd.Series,
) -> pd.DataFrame:
    """
    Filtra DataFrame para manter apenas dias de trading.

    Args:
        df: DataFrame com index de datas
        trading_dates: Datas válidas de trading

    Returns:
        DataFrame filtrado
    """
    if isinstance(trading_dates, pd.Series):
        trading_dates = pd.DatetimeIndex(trading_dates)

    return df.loc[df.index.isin(trading_dates)]


def create_analysis_dataset(
    iron_ore_df: pd.DataFrame,
    vale3_df: pd.DataFrame,
    auxiliary_df: pd.DataFrame | None = None,
    iron_price_col: str = "price",
    vale_price_col: str = "close",
    date_col: str = "date",
) -> pd.DataFrame:
    """
    Cria dataset consolidado para análise estatística.

    Implementa a estratégia de alinhamento:
    1. Cria range de datas completo
    2. Reindexar cada série
    3. Forward fill para gaps (mercados fechados)
    4. Filtrar apenas dias onde B3 operou (dias de decisão)

    Args:
        iron_ore_df: DataFrame com preços de minério
        vale3_df: DataFrame com preços de VALE3
        auxiliary_df: DataFrame com dados auxiliares (USD/BRL, VIX)
        iron_price_col: Coluna de preço do minério
        vale_price_col: Coluna de preço de VALE3
        date_col: Coluna de data

    Returns:
        DataFrame consolidado com todas as features
    """
    # Prepara índices
    iron = iron_ore_df.copy()
    vale = vale3_df.copy()

    if date_col in iron.columns:
        iron = iron.set_index(date_col)
    if date_col in vale.columns:
        vale = vale.set_index(date_col)

    # Determina range de datas
    all_dates = create_date_range(
        start=min(iron.index.min(), vale.index.min()),
        end=max(iron.index.max(), vale.index.max()),
    )

    # Seleciona colunas relevantes
    iron_data = iron[[iron_price_col]].rename(columns={iron_price_col: "iron_ore_price"})
    vale_data = vale[[vale_price_col]].rename(columns={vale_price_col: "vale3_close"})

    # Adiciona OHLV se disponíveis
    for col in ["open", "high", "low", "volume"]:
        if col in vale.columns:
            vale_data[f"vale3_{col}"] = vale[col]

    # Reindex com forward fill
    iron_filled = forward_fill_gaps(iron_data, all_dates)
    vale_filled = forward_fill_gaps(vale_data, all_dates)

    # Combina
    combined = pd.concat([iron_filled, vale_filled], axis=1)

    # Dados auxiliares
    if auxiliary_df is not None:
        aux = auxiliary_df.copy()
        if date_col in aux.columns:
            aux = aux.set_index(date_col)

        for col in ["usd_brl", "vix", "ibov"]:
            if col in aux.columns:
                aux_filled = forward_fill_gaps(aux[[col]], all_dates)
                combined = pd.concat([combined, aux_filled], axis=1)

    # Filtra apenas dias onde B3 operou
    b3_trading_days = vale.index
    combined = filter_trading_days(combined, b3_trading_days)

    # Remove linhas sem dados essenciais
    combined = combined.dropna(subset=["iron_ore_price", "vale3_close"])

    logger.info(
        f"Dataset de análise criado: {len(combined)} registros, "
        f"{combined.index.min().date()} a {combined.index.max().date()}"
    )

    return combined


def add_lagged_features(
    df: pd.DataFrame,
    source_col: str,
    target_col: str,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """
    Adiciona features defasadas de um ativo para prever outro.

    Para a estratégia minério → VALE3:
    - Retorno do minério de hoje (D0) é feature para VALE3 de amanhã (D+1)
    - Mas como dados são alinhados por dia, usamos lag=1

    Args:
        df: DataFrame com ambas as colunas
        source_col: Coluna fonte (ex: 'iron_ore_return_1d')
        target_col: Coluna alvo (ex: 'vale3_return_1d')
        lags: Defasagens a criar (default: [1, 2, 3])

    Returns:
        DataFrame com features defasadas

    Examples:
        >>> # Retorno do minério de D-1 como feature para VALE3 hoje
        >>> df = add_lagged_features(df, 'iron_return_1d', 'vale3_return_1d', lags=[1])
        >>> # df['iron_return_1d_lag_1'] contém retorno do minério de ontem
    """
    if lags is None:
        lags = [1, 2, 3]

    df = df.copy()

    for lag in lags:
        col_name = f"{source_col}_lag_{lag}"
        df[col_name] = df[source_col].shift(lag)

    return df


def calculate_lead_lag_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    max_lag: int = 10,
) -> pd.DataFrame:
    """
    Calcula correlação lead-lag entre duas séries.

    Identifica se série A lidera ou segue série B.

    Args:
        series_a: Primeira série (ex: retornos minério)
        series_b: Segunda série (ex: retornos VALE3)
        max_lag: Máximo de lags para testar

    Returns:
        DataFrame com correlações para cada lag:
        - lag > 0: série A lidera série B
        - lag < 0: série B lidera série A
    """
    results = []

    for lag in range(-max_lag, max_lag + 1):
        if lag == 0:
            corr = series_a.corr(series_b)
        elif lag > 0:
            # A lidera B por `lag` dias
            corr = series_a.shift(lag).corr(series_b)
        else:
            # B lidera A por `abs(lag)` dias
            corr = series_a.corr(series_b.shift(abs(lag)))

        results.append({
            "lag": lag,
            "correlation": corr,
            "leader": "A" if lag > 0 else ("B" if lag < 0 else "simultaneous"),
        })

    return pd.DataFrame(results)


def validate_alignment(df: pd.DataFrame) -> dict:
    """
    Valida qualidade do alinhamento de dados.

    Args:
        df: DataFrame alinhado

    Returns:
        Dict com métricas de qualidade:
        - total_rows: Total de registros
        - missing_pct: Percentual de valores faltantes por coluna
        - date_gaps: Número de gaps > 1 dia
        - date_range: Período coberto
    """
    result = {
        "total_rows": len(df),
        "date_range": {
            "start": df.index.min().isoformat() if len(df) > 0 else None,
            "end": df.index.max().isoformat() if len(df) > 0 else None,
        },
        "missing_pct": {},
        "date_gaps": 0,
    }

    # Percentual de missing por coluna
    for col in df.columns:
        missing_pct = (df[col].isna().sum() / len(df)) * 100
        result["missing_pct"][col] = round(missing_pct, 2)

    # Conta gaps no índice
    if len(df) > 1:
        date_diffs = df.index.to_series().diff()
        # Gaps maiores que 1 dia (considerando 3 dias para fins de semana)
        gaps = (date_diffs > pd.Timedelta(days=3)).sum()
        result["date_gaps"] = int(gaps)

    return result
