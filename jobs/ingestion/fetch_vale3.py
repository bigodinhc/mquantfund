"""
Fetcher de preços de VALE3 via LSEG Workspace.

Coleta dados de VALE3.SA na B3.

Horário de mercado B3 (BRT): 10:00-17:55
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
from jobs.config.settings import LSEG_CONFIG_PATH, VALE3_RIC

# Importa LSEG
try:
    import lseg.data as ld
except ImportError:
    logger.error("lseg-data não instalado. Execute: pip install lseg-data")
    ld = None


class Vale3Fetcher:
    """Fetcher de preços de VALE3 via LSEG."""

    def __init__(self) -> None:
        """Inicializa o fetcher."""
        self.supabase = get_supabase_client()
        self.ric = VALE3_RIC
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
        Busca snapshot de preço em tempo real de VALE3.

        Returns:
            Lista com um dict contendo dados de preço.
        """
        records = []

        try:
            if not self._open_session():
                return records

            # Campos que funcionam para ações brasileiras
            fields = [
                "TRDPRC_1",    # Último preço
                "BID",         # Bid
                "ASK",         # Ask
                "HIGH_1",      # High
                "LOW_1",       # Low
                "OPEN_PRC",    # Open
                "ACVOL_UNS",   # Volume
            ]

            logger.info(f"Buscando dados para {self.ric}")

            response = ld.get_data([self.ric], fields=fields)

            if response is None or response.empty:
                logger.warning(f"Sem dados retornados para {self.ric}")
                return records

            now_utc = datetime.now(timezone.utc)

            for _, row in response.iterrows():
                last_price = row.get("TRDPRC_1")

                if pd.isna(last_price):
                    logger.warning(f"Preço inválido para {self.ric}")
                    continue

                record = {
                    "timestamp": now_utc.isoformat(),
                    "close": float(last_price),
                }

                if not pd.isna(row.get("OPEN_PRC")):
                    record["open"] = float(row.get("OPEN_PRC"))
                if not pd.isna(row.get("HIGH_1")):
                    record["high"] = float(row.get("HIGH_1"))
                if not pd.isna(row.get("LOW_1")):
                    record["low"] = float(row.get("LOW_1"))
                if not pd.isna(row.get("ACVOL_UNS")):
                    record["volume"] = int(row.get("ACVOL_UNS"))

                records.append(record)
                logger.info(f"Coletado: VALE3 = {last_price}")

        except Exception as e:
            logger.error(f"Erro ao buscar dados realtime VALE3: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_vale3",
                message=f"Erro ao buscar dados realtime: {e}",
            )
        finally:
            self._close_session()

        return records

    def fetch_historical(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "daily",
    ) -> list[dict[str, Any]]:
        """
        Busca dados históricos de VALE3.

        Args:
            start_date: Data início (YYYY-MM-DD). Padrão: 30 dias atrás
            end_date: Data fim (YYYY-MM-DD). Padrão: hoje
            interval: Intervalo (1H, 1D, etc.)

        Returns:
            Lista de dicts com dados históricos.
        """
        records = []

        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_dt = datetime.now() - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")

        try:
            if not self._open_session():
                return records

            logger.info(f"Buscando histórico VALE3: {start_date} a {end_date}")

            response = ld.get_history(
                universe=self.ric,
                fields=["TRDPRC_1", "HIGH_1", "LOW_1", "OPEN_PRC", "ACVOL_UNS"],
                interval=interval,
                start=start_date,
                end=end_date,
            )

            if response is None or response.empty:
                logger.warning(f"Sem dados históricos para {self.ric}")
                return records

            for timestamp, row in response.iterrows():
                price = row.get("TRDPRC_1")
                if pd.isna(price):
                    continue

                if isinstance(timestamp, pd.Timestamp):
                    ts_utc = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
                else:
                    ts_utc = pd.Timestamp(timestamp, tz="UTC")

                record = {
                    "timestamp": ts_utc.isoformat(),
                    "close": float(price),
                }

                if not pd.isna(row.get("OPEN_PRC")):
                    record["open"] = float(row.get("OPEN_PRC"))
                if not pd.isna(row.get("HIGH_1")):
                    record["high"] = float(row.get("HIGH_1"))
                if not pd.isna(row.get("LOW_1")):
                    record["low"] = float(row.get("LOW_1"))
                if not pd.isna(row.get("ACVOL_UNS")):
                    record["volume"] = int(row.get("ACVOL_UNS"))

                records.append(record)

            logger.info(f"Coletados {len(records)} registros históricos VALE3")

        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos VALE3: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_vale3",
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
            return self.supabase.insert_vale3_prices(records)
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
            return self.supabase.insert_vale3_prices(records)
        return 0


def main() -> None:
    """Executa coleta de dados de VALE3."""
    import argparse

    parser = argparse.ArgumentParser(description="Coleta preços de VALE3")
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

    fetcher = Vale3Fetcher()

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
