"""
Atualização semanal de métricas.
Executa via GitHub Actions aos domingos.
"""

from datetime import date, datetime, timedelta

import numpy as np
from loguru import logger

from src.analysis.weekly_correlation import calculate_correlation
from src.db.client import get_supabase


def calculate_sharpe_ratio(returns: list[float], risk_free_rate: float = 0.1075) -> float:
    """
    Calcula Sharpe Ratio anualizado.

    Args:
        returns: Lista de retornos diários.
        risk_free_rate: Taxa livre de risco anual (default: SELIC ~10.75%).

    Returns:
        Sharpe Ratio anualizado.
    """
    if len(returns) < 2:
        return 0.0

    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_returns = [r - daily_rf for r in returns]

    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns)

    if std_excess == 0:
        return 0.0

    return float(mean_excess / std_excess * np.sqrt(252))


def calculate_max_drawdown(equity_curve: list[float]) -> float:
    """
    Calcula máximo drawdown.

    Args:
        equity_curve: Lista de valores do patrimônio.

    Returns:
        Máximo drawdown como fração (ex: 0.15 = 15%).
    """
    if len(equity_curve) < 2:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        max_dd = max(max_dd, drawdown)

    return float(max_dd)


def update_weekly_metrics() -> dict:
    """
    Atualiza métricas semanais no banco.

    Returns:
        Dicionário com métricas calculadas.
    """
    client = get_supabase()

    # Período: última semana
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # Buscar posições fechadas na semana
    positions_result = client.table("positions").select("*").eq(
        "status", "CLOSED"
    ).gte(
        "exit_timestamp", start_date.isoformat()
    ).execute()

    positions = positions_result.data or []

    # Calcular retornos
    returns = []
    equity = [50000]  # Capital inicial (TODO: pegar do config)

    for pos in sorted(positions, key=lambda x: x.get("exit_timestamp", "")):
        pnl = pos.get("realized_pnl", 0) or 0
        if equity[-1] > 0:
            ret = pnl / equity[-1]
            returns.append(ret)
            equity.append(equity[-1] + pnl)

    # Métricas
    sharpe = calculate_sharpe_ratio(returns) if returns else 0
    max_dd = calculate_max_drawdown(equity)
    total_pnl = sum(p.get("realized_pnl", 0) or 0 for p in positions)
    winning = len([p for p in positions if (p.get("realized_pnl", 0) or 0) > 0])
    total = len(positions)

    # Correlação
    corr_data = calculate_correlation(30)
    correlation = corr_data.get("correlation_pearson", 0) or 0

    metrics = {
        "week_start": start_date.isoformat(),
        "week_end": end_date.isoformat(),
        "trades_count": total,
        "winning_trades": winning,
        "win_rate": winning / total if total > 0 else 0,
        "total_pnl": total_pnl,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "correlation_iron_vale": correlation,
    }

    # Salvar log
    client.table("system_logs").insert({
        "level": "INFO",
        "component": "update_weekly",
        "message": f"Métricas semanais: Sharpe={sharpe:.2f}, MaxDD={max_dd:.2%}",
        "details": metrics,
    }).execute()

    logger.info(f"Métricas atualizadas: {metrics}")
    return metrics


def main():
    """Entry point para execução via CLI."""
    logger.info("Atualizando métricas semanais...")
    metrics = update_weekly_metrics()
    logger.info(f"Concluído: {metrics}")


if __name__ == "__main__":
    main()
