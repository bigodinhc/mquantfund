"""
Análise semanal de correlação Minério x VALE3.
Executa via GitHub Actions aos domingos.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

from src.db.client import get_supabase


def calculate_correlation(days: int = 60) -> dict:
    """
    Calcula correlação entre minério de ferro e VALE3.

    Args:
        days: Número de dias para análise.

    Returns:
        Dicionário com métricas de correlação.
    """
    client = get_supabase()
    since = datetime.now() - timedelta(days=days)

    # Buscar preços de minério
    iron_result = client.table("prices_iron_ore").select(
        "timestamp, close, price"
    ).gte(
        "timestamp", since.isoformat()
    ).order("timestamp").execute()

    # Buscar preços de VALE3
    vale_result = client.table("prices_vale3").select(
        "timestamp, close"
    ).gte(
        "timestamp", since.isoformat()
    ).order("timestamp").execute()

    iron_data = iron_result.data or []
    vale_data = vale_result.data or []

    if len(iron_data) < 10 or len(vale_data) < 10:
        logger.warning("Dados insuficientes para calcular correlação")
        return {
            "correlation": None,
            "p_value": None,
            "iron_count": len(iron_data),
            "vale_count": len(vale_data),
            "error": "Dados insuficientes",
        }

    # Converter para DataFrames
    iron_df = pd.DataFrame(iron_data)
    iron_df["timestamp"] = pd.to_datetime(iron_df["timestamp"])
    iron_df["price"] = iron_df["close"].fillna(iron_df["price"])
    iron_df = iron_df.set_index("timestamp")["price"].resample("D").last().dropna()

    vale_df = pd.DataFrame(vale_data)
    vale_df["timestamp"] = pd.to_datetime(vale_df["timestamp"])
    vale_df = vale_df.set_index("timestamp")["close"].resample("D").last().dropna()

    # Alinhar séries
    combined = pd.DataFrame({
        "iron": iron_df,
        "vale": vale_df,
    }).dropna()

    if len(combined) < 10:
        return {
            "correlation": None,
            "p_value": None,
            "aligned_count": len(combined),
            "error": "Dados alinhados insuficientes",
        }

    # Calcular retornos
    returns = combined.pct_change().dropna()

    # Correlação de Pearson
    correlation, p_value = stats.pearsonr(returns["iron"], returns["vale"])

    # Correlação de Spearman (mais robusta)
    spearman_corr, spearman_p = stats.spearmanr(returns["iron"], returns["vale"])

    # Beta (sensibilidade de VALE3 ao minério)
    cov = np.cov(returns["iron"], returns["vale"])[0, 1]
    var_iron = np.var(returns["iron"])
    beta = cov / var_iron if var_iron > 0 else 0

    return {
        "correlation_pearson": float(correlation),
        "correlation_spearman": float(spearman_corr),
        "p_value": float(p_value),
        "beta": float(beta),
        "days_analyzed": days,
        "data_points": len(combined),
        "iron_volatility": float(returns["iron"].std() * np.sqrt(252)),
        "vale_volatility": float(returns["vale"].std() * np.sqrt(252)),
    }


def calculate_lead_lag(max_lag: int = 5) -> dict:
    """
    Análise de lead-lag entre minério e VALE3.

    Args:
        max_lag: Número máximo de lags a testar.

    Returns:
        Dicionário com análise de lead-lag.
    """
    client = get_supabase()
    since = datetime.now() - timedelta(days=90)

    # Buscar dados
    iron_result = client.table("prices_iron_ore").select(
        "timestamp, close, price"
    ).gte("timestamp", since.isoformat()).order("timestamp").execute()

    vale_result = client.table("prices_vale3").select(
        "timestamp, close"
    ).gte("timestamp", since.isoformat()).order("timestamp").execute()

    iron_data = iron_result.data or []
    vale_data = vale_result.data or []

    if len(iron_data) < 20 or len(vale_data) < 20:
        return {"error": "Dados insuficientes"}

    # Preparar séries
    iron_df = pd.DataFrame(iron_data)
    iron_df["timestamp"] = pd.to_datetime(iron_df["timestamp"])
    iron_df["price"] = iron_df["close"].fillna(iron_df["price"])
    iron_series = iron_df.set_index("timestamp")["price"].resample("D").last().dropna()

    vale_df = pd.DataFrame(vale_data)
    vale_df["timestamp"] = pd.to_datetime(vale_df["timestamp"])
    vale_series = vale_df.set_index("timestamp")["close"].resample("D").last().dropna()

    # Calcular retornos
    iron_returns = iron_series.pct_change().dropna()
    vale_returns = vale_series.pct_change().dropna()

    # Cross-correlation para diferentes lags
    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # VALE3 lidera (improvável)
            aligned_iron = iron_returns.iloc[-lag:]
            aligned_vale = vale_returns.iloc[:lag]
        elif lag > 0:
            # Minério lidera (esperado)
            aligned_iron = iron_returns.iloc[:-lag]
            aligned_vale = vale_returns.iloc[lag:]
        else:
            aligned_iron = iron_returns
            aligned_vale = vale_returns

        # Alinhar por data
        common_dates = aligned_iron.index.intersection(aligned_vale.index)
        if len(common_dates) < 10:
            continue

        corr, _ = stats.pearsonr(
            aligned_iron.loc[common_dates],
            aligned_vale.loc[common_dates]
        )
        correlations[lag] = float(corr)

    # Encontrar lag ótimo
    if correlations:
        optimal_lag = max(correlations, key=lambda x: abs(correlations[x]))
        optimal_corr = correlations[optimal_lag]
    else:
        optimal_lag = 0
        optimal_corr = 0

    return {
        "correlations_by_lag": correlations,
        "optimal_lag_days": optimal_lag,
        "optimal_correlation": optimal_corr,
        "interpretation": (
            f"Minério lidera VALE3 em {optimal_lag} dia(s)"
            if optimal_lag > 0
            else "Correlação contemporânea"
        ),
    }


def main():
    """Entry point para execução via CLI."""
    logger.info("Executando análise semanal de correlação...")

    # Calcular correlação
    corr_metrics = calculate_correlation(60)
    logger.info(f"Correlação Pearson: {corr_metrics.get('correlation_pearson', 'N/A')}")
    logger.info(f"Beta: {corr_metrics.get('beta', 'N/A')}")

    # Análise lead-lag
    lead_lag = calculate_lead_lag(5)
    logger.info(f"Lag ótimo: {lead_lag.get('optimal_lag_days', 'N/A')} dias")

    # Salvar no banco
    client = get_supabase()
    client.table("system_logs").insert({
        "level": "INFO",
        "component": "weekly_correlation",
        "message": "Análise semanal concluída",
        "details": {
            "correlation": corr_metrics,
            "lead_lag": lead_lag,
        },
    }).execute()

    logger.info("Análise semanal concluída")


if __name__ == "__main__":
    main()
