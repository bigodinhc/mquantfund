"""
Gerador de sinais de trading para estratégia VALE3-Minério.

Implementa a estratégia rule-based:
- LONG: Retorno minério > 1.5 * std_20d, direção consistente, USD/BRL estável
- SHORT: Retorno minério < -1.5 * std_20d, direção consistente, USD/BRL estável

Filtros NO-TRADE:
- VIX > 25
- Gap abertura B3 > 2%
- Correlação rolling 20d < 0.2
- Feriado em BR, SG ou CN
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from src.config import (
    CORRELATION_THRESHOLD,
    ROLLING_WINDOW,
    SIGNAL_THRESHOLD_STD,
    TELEGRAM_BOT_TOKEN,
)
from src.db.client import get_supabase, save_signal


class SignalGenerator:
    """Gerador de sinais de trading."""

    def __init__(self) -> None:
        """Inicializa o gerador."""
        self.client = get_supabase()
        self.rolling_window = ROLLING_WINDOW
        self.signal_threshold = SIGNAL_THRESHOLD_STD
        self.correlation_threshold = CORRELATION_THRESHOLD

    def get_recent_iron_ore_prices(self, days: int = 30) -> pd.DataFrame:
        """
        Busca preços recentes de minério de ferro.

        Args:
            days: Número de dias para buscar.

        Returns:
            DataFrame com preços.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            result = (
                self.client.table("prices_iron_ore")
                .select("timestamp, price, symbol")
                .gte("timestamp", since.isoformat())
                .order("timestamp", desc=False)
                .execute()
            )

            if not result.data:
                return pd.DataFrame()

            df = pd.DataFrame(result.data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            return df

        except Exception as e:
            logger.error(f"Erro ao buscar preços minério: {e}")
            return pd.DataFrame()

    def get_recent_vale3_prices(self, days: int = 30) -> pd.DataFrame:
        """
        Busca preços recentes de VALE3.

        Args:
            days: Número de dias para buscar.

        Returns:
            DataFrame com preços.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        try:
            result = (
                self.client.table("prices_vale3")
                .select("timestamp, close")
                .gte("timestamp", since.isoformat())
                .order("timestamp", desc=False)
                .execute()
            )

            if not result.data:
                return pd.DataFrame()

            df = pd.DataFrame(result.data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            return df

        except Exception as e:
            logger.error(f"Erro ao buscar preços VALE3: {e}")
            return pd.DataFrame()

    def get_latest_auxiliary_data(self) -> dict[str, float]:
        """
        Busca dados auxiliares mais recentes.

        Returns:
            Dict com usd_brl, vix, ibov.
        """
        try:
            result = (
                self.client.table("auxiliary_data")
                .select("*")
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return result.data[0]
            return {}

        except Exception as e:
            logger.error(f"Erro ao buscar dados auxiliares: {e}")
            return {}

    def calculate_iron_ore_return(self, df: pd.DataFrame) -> tuple[float, float, float]:
        """
        Calcula retorno e z-score do minério de ferro.

        Args:
            df: DataFrame com preços.

        Returns:
            Tuple (retorno_atual, std_20d, zscore).
        """
        if df.empty or len(df) < self.rolling_window + 1:
            return 0.0, 0.0, 0.0

        # Pega preços de fechamento diário (agrupa por dia)
        daily = df.groupby(df.index.date)["price"].last()

        if len(daily) < self.rolling_window + 1:
            return 0.0, 0.0, 0.0

        # Calcula retornos
        returns = daily.pct_change().dropna()

        if len(returns) < self.rolling_window:
            return 0.0, 0.0, 0.0

        # Retorno atual e volatilidade histórica
        current_return = returns.iloc[-1]
        historical_std = returns.iloc[-self.rolling_window - 1 : -1].std()

        if historical_std == 0 or np.isnan(historical_std):
            return current_return, 0.0, 0.0

        zscore = current_return / historical_std

        return current_return, historical_std, zscore

    def check_direction_consistency(self, df: pd.DataFrame, hours: int = 2) -> bool:
        """
        Verifica se a direção do preço foi consistente nas últimas N horas.

        Args:
            df: DataFrame com preços.
            hours: Número de horas para verificar.

        Returns:
            True se direção consistente.
        """
        if df.empty:
            return False

        # Filtra últimas N horas
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = df[df.index >= cutoff]

        if len(recent) < 2:
            return True  # Sem dados suficientes, assume consistente

        # Verifica se todos os retornos têm o mesmo sinal
        returns = recent["price"].pct_change().dropna()

        if len(returns) == 0:
            return True

        # Direção consistente se todos positivos ou todos negativos
        all_positive = (returns >= 0).all()
        all_negative = (returns <= 0).all()

        return all_positive or all_negative

    def calculate_correlation(
        self, iron_ore: pd.DataFrame, vale3: pd.DataFrame
    ) -> float:
        """
        Calcula correlação rolling entre minério e VALE3.

        Args:
            iron_ore: DataFrame de preços do minério.
            vale3: DataFrame de preços VALE3.

        Returns:
            Correlação rolling.
        """
        if iron_ore.empty or vale3.empty:
            return 0.0

        # Agrupa por dia
        io_daily = iron_ore.groupby(iron_ore.index.date)["price"].last()
        vale_daily = vale3.groupby(vale3.index.date)["close"].last()

        # Alinha datas
        combined = pd.DataFrame({"iron_ore": io_daily, "vale3": vale_daily}).dropna()

        if len(combined) < self.rolling_window:
            return 0.0

        # Calcula correlação dos retornos
        returns = combined.pct_change().dropna()

        if len(returns) < self.rolling_window:
            return 0.0

        correlation = returns["iron_ore"].corr(returns["vale3"])

        return correlation if not np.isnan(correlation) else 0.0

    def check_no_trade_conditions(self, auxiliary: dict[str, float]) -> tuple[bool, str]:
        """
        Verifica condições de NO-TRADE.

        Args:
            auxiliary: Dados auxiliares.

        Returns:
            Tuple (should_trade, reason).
        """
        # VIX > 25
        vix = auxiliary.get("vix", 0)
        if vix and vix > 25:
            return False, f"VIX muito alto ({vix:.1f} > 25)"

        # TODO: Adicionar verificação de feriados
        # TODO: Adicionar verificação de gap de abertura
        # TODO: Adicionar verificação de anúncios macro

        return True, ""

    def generate_signal(self) -> dict[str, Any] | None:
        """
        Gera sinal de trading baseado nas condições atuais.

        Returns:
            Dict com detalhes do sinal ou None se sem sinal.
        """
        logger.info("Iniciando geração de sinal...")

        # Buscar dados
        iron_ore_df = self.get_recent_iron_ore_prices(days=self.rolling_window + 5)
        vale3_df = self.get_recent_vale3_prices(days=self.rolling_window + 5)
        auxiliary = self.get_latest_auxiliary_data()

        if iron_ore_df.empty:
            logger.warning("Sem dados de minério de ferro disponíveis")
            return None

        # Verificar condições de NO-TRADE
        should_trade, no_trade_reason = self.check_no_trade_conditions(auxiliary)
        if not should_trade:
            logger.info(f"NO-TRADE: {no_trade_reason}")
            return None

        # Calcular métricas do minério
        current_return, std_20d, zscore = self.calculate_iron_ore_return(iron_ore_df)

        if std_20d == 0:
            logger.warning("Volatilidade zero - sem dados suficientes")
            return None

        # Verificar correlação
        correlation = self.calculate_correlation(iron_ore_df, vale3_df)
        if correlation < self.correlation_threshold:
            logger.info(
                f"NO-TRADE: Correlação baixa ({correlation:.2f} < {self.correlation_threshold})"
            )
            return None

        # Verificar direção consistente
        direction_consistent = self.check_direction_consistency(iron_ore_df, hours=2)

        # Verificar variação USD/BRL
        usd_brl_variation = abs(auxiliary.get("usd_brl_change", 0) or 0)

        # Calcular sinal
        signal_type = None
        confidence = 0.0

        threshold = self.signal_threshold * std_20d

        if current_return > threshold:
            if direction_consistent and usd_brl_variation < 0.005:  # < 0.5%
                signal_type = "LONG"
                confidence = min(abs(zscore) / 3.0, 1.0)  # Normaliza confiança

        elif current_return < -threshold:
            if direction_consistent and usd_brl_variation < 0.005:
                signal_type = "SHORT"
                confidence = min(abs(zscore) / 3.0, 1.0)

        if signal_type is None:
            logger.info(
                f"Sem sinal: zscore={zscore:.2f}, threshold=±{self.signal_threshold}"
            )
            return None

        # Construir sinal
        signal = {
            "timestamp": datetime.now(timezone.utc),
            "signal_type": signal_type,
            "confidence": confidence,
            "iron_ore_return": current_return,
            "iron_ore_zscore": zscore,
            "iron_ore_std_20d": std_20d,
            "correlation": correlation,
            "vix": auxiliary.get("vix"),
            "usd_brl": auxiliary.get("usd_brl"),
        }

        logger.info(
            f"SINAL GERADO: {signal_type} (confiança={confidence:.1%}, zscore={zscore:.2f})"
        )

        return signal

    def process_and_save_signal(self) -> dict[str, Any] | None:
        """
        Gera sinal, salva no banco e notifica.

        Returns:
            Sinal gerado ou None.
        """
        signal = self.generate_signal()

        if signal is None:
            return None

        # Salvar no banco
        saved = save_signal(
            timestamp=signal["timestamp"],
            signal_type=signal["signal_type"],
            confidence=signal["confidence"],
            iron_ore_return=signal["iron_ore_return"],
            iron_ore_zscore=signal["iron_ore_zscore"],
            features={
                "std_20d": signal["iron_ore_std_20d"],
                "correlation": signal["correlation"],
                "vix": signal["vix"],
                "usd_brl": signal["usd_brl"],
            },
        )

        if saved:
            logger.info(f"Sinal salvo: ID={saved.get('id')}")

            # Notificar via Telegram
            if TELEGRAM_BOT_TOKEN:
                asyncio.run(self._notify_signal(signal))

        return signal

    async def _notify_signal(self, signal: dict[str, Any]) -> None:
        """Envia notificação de sinal via Telegram."""
        try:
            from src.notifications.telegram_bot import send_signal_alert

            await send_signal_alert(
                signal_type=signal["signal_type"],
                confidence=signal["confidence"],
                zscore=signal["iron_ore_zscore"],
            )
        except Exception as e:
            logger.error(f"Erro ao notificar sinal: {e}")


def main() -> None:
    """Entry point para execução via CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Gerador de sinais de trading")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gera sinal sem salvar no banco",
    )
    args = parser.parse_args()

    generator = SignalGenerator()

    if args.dry_run:
        signal = generator.generate_signal()
        if signal:
            print(f"Sinal: {signal['signal_type']}")
            print(f"Confiança: {signal['confidence']:.1%}")
            print(f"Z-Score: {signal['iron_ore_zscore']:.2f}")
        else:
            print("Nenhum sinal gerado")
    else:
        signal = generator.process_and_save_signal()
        if signal:
            print(f"Sinal {signal['signal_type']} gerado e salvo")
        else:
            print("Nenhum sinal gerado")


if __name__ == "__main__":
    main()
