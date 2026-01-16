"""
Bot Telegram para notificações do QuantFund.
Envia alertas de sinais, ordens e relatórios.
"""

import argparse
import asyncio

from loguru import logger

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.reports.daily_report import generate_report_text, get_daily_metrics


async def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Envia mensagem via Telegram.

    Args:
        text: Texto da mensagem.
        parse_mode: Modo de parse (Markdown, HTML).

    Returns:
        True se enviou com sucesso.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram não configurado. Pulando envio.")
        return False

    try:
        from telegram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=parse_mode,
        )
        logger.info("Mensagem enviada via Telegram")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem Telegram: {e}")
        return False


async def send_signal_alert(
    signal_type: str,
    confidence: float,
    zscore: float,
) -> bool:
    """Envia alerta de novo sinal."""
    emoji = "🟢" if signal_type == "LONG" else "🔴" if signal_type == "SHORT" else "⚪"

    message = f"""
{emoji} *SINAL DETECTADO*

*Tipo:* {signal_type}
*Confiança:* {confidence:.1%}
*Z-Score Minério:* {zscore:.2f}

_Aguardando confirmação para execução..._
"""
    return await send_message(message.strip())


async def send_order_alert(
    side: str,
    quantity: int,
    price: float,
    status: str,
) -> bool:
    """Envia alerta de ordem."""
    emoji = "📈" if side == "BUY" else "📉"

    message = f"""
{emoji} *ORDEM {status}*

*Lado:* {side}
*Quantidade:* {quantity}
*Preço:* R$ {price:.2f}
"""
    return await send_message(message.strip())


async def send_daily_report() -> bool:
    """Envia relatório diário."""
    metrics = get_daily_metrics()
    report = generate_report_text(metrics)
    return await send_message(report)


async def send_kill_switch_alert(level: int, reason: str) -> bool:
    """Envia alerta de kill switch."""
    message = f"""
🚨 *KILL SWITCH ATIVADO*

*Nível:* {level}
*Motivo:* {reason}

_Sistema pausado. Verificar imediatamente._
"""
    return await send_message(message.strip())


def main():
    """Entry point para execução via CLI."""
    parser = argparse.ArgumentParser(description="Telegram Bot")
    parser.add_argument(
        "--send-daily-report",
        action="store_true",
        help="Envia relatório diário",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Envia mensagem de teste",
    )

    args = parser.parse_args()

    if args.send_daily_report:
        asyncio.run(send_daily_report())
    elif args.test:
        asyncio.run(send_message("🤖 *QuantFund* - Teste de conexão OK!"))
    else:
        print("Use --send-daily-report ou --test")


if __name__ == "__main__":
    main()
