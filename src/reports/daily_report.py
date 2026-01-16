"""
Gerador de relatório diário.
Executa via GitHub Actions às 22:00 UTC.
"""

from datetime import date, datetime, timedelta

from loguru import logger

from src.db.client import get_supabase


def get_daily_metrics(target_date: date | None = None) -> dict:
    """
    Coleta métricas do dia.

    Args:
        target_date: Data alvo (default: hoje)

    Returns:
        Dicionário com métricas do dia.
    """
    if target_date is None:
        target_date = date.today()

    client = get_supabase()

    # Buscar sinais do dia
    signals_result = client.table("signals").select("*").gte(
        "timestamp", target_date.isoformat()
    ).lt(
        "timestamp", (target_date + timedelta(days=1)).isoformat()
    ).execute()

    signals = signals_result.data or []

    # Buscar ordens do dia
    orders_result = client.table("orders").select("*").gte(
        "timestamp", target_date.isoformat()
    ).lt(
        "timestamp", (target_date + timedelta(days=1)).isoformat()
    ).execute()

    orders = orders_result.data or []

    # Buscar posições fechadas hoje
    positions_result = client.table("positions").select("*").eq(
        "status", "CLOSED"
    ).gte(
        "exit_timestamp", target_date.isoformat()
    ).execute()

    closed_positions = positions_result.data or []

    # Calcular métricas
    total_pnl = sum(p.get("realized_pnl", 0) or 0 for p in closed_positions)
    winning = len([p for p in closed_positions if (p.get("realized_pnl", 0) or 0) > 0])
    losing = len([p for p in closed_positions if (p.get("realized_pnl", 0) or 0) < 0])

    return {
        "date": target_date.isoformat(),
        "signals_generated": len(signals),
        "signals_long": len([s for s in signals if s.get("signal_type") == "LONG"]),
        "signals_short": len([s for s in signals if s.get("signal_type") == "SHORT"]),
        "orders_sent": len(orders),
        "orders_filled": len([o for o in orders if o.get("status") == "FILLED"]),
        "positions_closed": len(closed_positions),
        "winning_trades": winning,
        "losing_trades": losing,
        "win_rate": winning / len(closed_positions) if closed_positions else 0,
        "total_pnl": total_pnl,
    }


def generate_report_text(metrics: dict) -> str:
    """
    Gera texto do relatório.

    Args:
        metrics: Dicionário com métricas.

    Returns:
        Texto formatado do relatório.
    """
    win_rate_pct = metrics["win_rate"] * 100

    report = f"""
📊 *RELATÓRIO DIÁRIO - {metrics['date']}*

*Sinais Gerados:* {metrics['signals_generated']}
  • LONG: {metrics['signals_long']}
  • SHORT: {metrics['signals_short']}

*Ordens:*
  • Enviadas: {metrics['orders_sent']}
  • Executadas: {metrics['orders_filled']}

*Operações:*
  • Fechadas: {metrics['positions_closed']}
  • Ganhadoras: {metrics['winning_trades']}
  • Perdedoras: {metrics['losing_trades']}
  • Win Rate: {win_rate_pct:.1f}%

*P&L do Dia:* R$ {metrics['total_pnl']:,.2f}

---
_QuantFund - Sistema Automatizado_
"""
    return report.strip()


def save_daily_metrics(metrics: dict) -> bool:
    """Salva métricas no banco."""
    client = get_supabase()

    try:
        client.table("daily_metrics").upsert({
            "date": metrics["date"],
            "daily_pnl": metrics["total_pnl"],
            "trades_count": metrics["positions_closed"],
            "winning_trades": metrics["winning_trades"],
            "losing_trades": metrics["losing_trades"],
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar métricas: {e}")
        return False


def main():
    """Entry point para execução via CLI."""
    logger.info("Gerando relatório diário...")

    metrics = get_daily_metrics()
    report = generate_report_text(metrics)

    print(report)

    # Salvar no banco
    save_daily_metrics(metrics)

    logger.info("Relatório gerado com sucesso")


if __name__ == "__main__":
    main()
