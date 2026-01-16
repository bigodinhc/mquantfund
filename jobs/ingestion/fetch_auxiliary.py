"""
Fetcher de dados auxiliares via LSEG Workspace.

Coleta:
- USD/BRL (câmbio)
- VIX (índice de volatilidade)

Esses dados são usados como filtros para a estratégia:
- VIX > 25 = NO-TRADE
- USD/BRL variação > 0.5% = NO-TRADE
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobs.clients.supabase_client import get_supabase_client
from jobs.config.settings import LSEG_CONFIG_PATH, USDBRL_RIC, VIX_RIC

# Importa LSEG
try:
    import lseg.data as ld
except ImportError:
    logger.error("lseg-data não instalado. Execute: pip install lseg-data")
    ld = None


class AuxiliaryFetcher:
    """Fetcher de dados auxiliares via LSEG."""

    def __init__(self) -> None:
        """Inicializa o fetcher."""
        self.supabase = get_supabase_client()
        self.session_open = False

    def _open_session(self) -> bool:
        """
        Abre sessão com LSEG Workspace usando arquivo de configuração.

        Returns:
            True se sessão aberta com sucesso.
        """
        if ld is None:
            logger.error("lseg-data não está instalado")
            return False

        try:
            config_path = LSEG_CONFIG_PATH
            if not config_path.exists():
                logger.error(f"Arquivo de configuração não encontrado: {config_path}")
                return False

            logger.info(f"Abrindo sessão LSEG com config: {config_path.name}")
            ld.open_session(config_name=str(config_path))
            self.session_open = True
            logger.info("Sessão LSEG aberta com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao abrir sessão LSEG: {e}")
            return False

    def _close_session(self) -> None:
        """Fecha sessão com LSEG."""
        if self.session_open:
            try:
                ld.close_session()
                logger.info("Sessão LSEG fechada")
            except Exception as e:
                logger.warning(f"Erro ao fechar sessão LSEG: {e}")
            finally:
                self.session_open = False

    def fetch_realtime(self) -> list[dict[str, Any]]:
        """
        Busca snapshot de USD/BRL e VIX em tempo real.

        Returns:
            Lista de dicts com dados (formato indicator/value).
        """
        records = []
        rics = [USDBRL_RIC, VIX_RIC]

        try:
            if not self._open_session():
                return records

            # Campos que funcionam para FX e índices
            fields = ["TRDPRC_1", "BID", "ASK"]

            logger.info(f"Buscando dados para {rics}")

            response = ld.get_data(rics, fields=fields)

            if response is None or response.empty:
                logger.warning(f"Sem dados retornados para {rics}")
                return records

            now_utc = datetime.now(timezone.utc)

            for _, row in response.iterrows():
                ric = row.get("Instrument", "")
                # Usa TRDPRC_1, ou média de BID/ASK como fallback
                last_value = row.get("TRDPRC_1")
                if pd.isna(last_value):
                    bid = row.get("BID")
                    ask = row.get("ASK")
                    if not pd.isna(bid) and not pd.isna(ask):
                        last_value = (float(bid) + float(ask)) / 2
                    elif not pd.isna(bid):
                        last_value = bid

                if pd.isna(last_value):
                    logger.warning(f"Valor inválido para {ric}")
                    continue

                # Mapeia RIC para nome do indicador
                if ric == USDBRL_RIC:
                    indicator = "usd_brl"
                elif ric == VIX_RIC:
                    indicator = "vix"
                else:
                    logger.warning(f"RIC desconhecido: {ric}")
                    continue

                record = {
                    "timestamp": now_utc.isoformat(),
                    "indicator": indicator,
                    "value": float(last_value),
                }
                records.append(record)
                logger.debug(f"Coletado: {indicator} = {last_value}")

            logger.info(f"Coletados {len(records)} indicadores auxiliares")

        except Exception as e:
            logger.error(f"Erro ao buscar dados auxiliares: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_auxiliary",
                message=f"Erro ao buscar dados realtime: {e}",
            )
        finally:
            self._close_session()

        return records

    def fetch_historical(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "1D",
    ) -> list[dict[str, Any]]:
        """
        Busca dados históricos de USD/BRL e VIX.

        Args:
            start_date: Data início (YYYY-MM-DD). Padrão: 30 dias atrás
            end_date: Data fim (YYYY-MM-DD). Padrão: hoje
            interval: Intervalo (1H, 1D, etc.)

        Returns:
            Lista de dicts com dados históricos (formato indicator/value).
        """
        records = []
        rics_map = {
            USDBRL_RIC: "usd_brl",
            VIX_RIC: "vix",
        }

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_dt = datetime.now() - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")

        try:
            if not self._open_session():
                return records

            for ric, indicator in rics_map.items():
                logger.info(f"Buscando histórico {indicator}: {start_date} a {end_date}")

                # LSEG usa campos diferentes para cada tipo de instrumento
                # Para FX/índices, busca sem especificar campos para usar default
                response = ld.get_history(
                    universe=ric,
                    interval=interval,
                    start=start_date,
                    end=end_date,
                )

                if response is None or response.empty:
                    logger.warning(f"Sem dados históricos para {indicator}")
                    continue

                count = 0
                # Detecta a coluna de preço disponível
                # FX usa MID_PRICE, índices usam CLOSE ou TRDPRC_1
                price_cols = ["MID_PRICE", "CLOSE", "TRDPRC_1", "MID_CLOSE", "BID", "BID_CLOSE", "ASK_CLOSE"]
                available_col = None
                for col in price_cols:
                    if col in response.columns:
                        available_col = col
                        break

                if not available_col:
                    # Usa primeira coluna numérica se nenhuma padrão encontrada
                    for col in response.columns:
                        if response[col].dtype in ['float64', 'int64']:
                            available_col = col
                            break

                if not available_col:
                    logger.warning(f"Sem coluna de preço válida para {indicator}. Colunas: {response.columns.tolist()}")
                    continue

                logger.info(f"Usando coluna '{available_col}' para {indicator}")

                for timestamp, row in response.iterrows():
                    value = row.get(available_col)
                    if pd.isna(value):
                        continue

                    if isinstance(timestamp, pd.Timestamp):
                        ts_utc = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
                    else:
                        ts_utc = pd.Timestamp(timestamp, tz="UTC")

                    record = {
                        "timestamp": ts_utc.isoformat(),
                        "indicator": indicator,
                        "value": float(value),
                    }
                    records.append(record)
                    count += 1

                logger.info(f"Coletados {count} registros para {indicator}")

        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos auxiliares: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_auxiliary",
                message=f"Erro ao buscar dados históricos: {e}",
            )
        finally:
            self._close_session()

        return records

    def fetch_and_persist_realtime(self) -> int:
        """
        Busca dados realtime e persiste no Supabase.

        Returns:
            Número de registros inseridos.
        """
        records = self.fetch_realtime()
        if records:
            return self.supabase.insert_auxiliary_data(records)
        return 0

    def fetch_and_persist_historical(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> int:
        """
        Busca dados históricos e persiste no Supabase.

        Args:
            start_date: Data início (YYYY-MM-DD)
            end_date: Data fim (YYYY-MM-DD)

        Returns:
            Número de registros inseridos.
        """
        records = self.fetch_historical(start_date=start_date, end_date=end_date)
        if records:
            return self.supabase.insert_auxiliary_data(records)
        return 0


def main() -> None:
    """Executa coleta de dados auxiliares."""
    import argparse

    parser = argparse.ArgumentParser(description="Coleta dados auxiliares (USD/BRL, VIX)")
    parser.add_argument(
        "--mode",
        choices=["realtime", "historical", "backfill"],
        default="realtime",
        help="Modo de coleta",
    )
    parser.add_argument(
        "--start-date",
        help="Data início para histórico (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="Data fim para histórico (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    fetcher = AuxiliaryFetcher()

    if args.mode == "realtime":
        count = fetcher.fetch_and_persist_realtime()
        logger.info(f"Coleta realtime concluída: {count} registros")

    elif args.mode in ("historical", "backfill"):
        count = fetcher.fetch_and_persist_historical(
            start_date=args.start_date,
            end_date=args.end_date,
        )
        logger.info(f"Coleta histórica concluída: {count} registros")


if __name__ == "__main__":
    main()
