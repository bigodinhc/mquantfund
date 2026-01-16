"""
Fetcher de preços de minério de ferro via LSEG Workspace.

Coleta dados de futuros SGX Iron Ore 62% Fe CFR China.
RICs: SZZC1 (front month), SZZC2, SZZC3

Horários de mercado (BRT):
- SGX T-Session:   20:25-09:00
- SGX T+1 Session: 09:00-17:45
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobs.clients.supabase_client import get_supabase_client
from jobs.config.settings import (
    IRON_ORE_RICS,
    LSEG_CONFIG_PATH,
    expiry_date_to_variable_key,
    ric_to_variable_key,
)

# Importa LSEG
try:
    import lseg.data as ld
except ImportError:
    logger.error("lseg-data não instalado. Execute: pip install lseg-data")
    ld = None


class IronOreFetcher:
    """Fetcher de preços de minério de ferro via LSEG."""

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

    def fetch_realtime(self, rics: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Busca snapshot de preços em tempo real.

        Args:
            rics: Lista de RICs a buscar. Padrão: IRON_ORE_RICS (12 meses)

        Returns:
            Lista de dicts com dados de preços.
        """
        rics = rics or IRON_ORE_RICS
        records = []

        try:
            if not self._open_session():
                return records

            # Campos a buscar (SETTLE e TRDPRC_1 funcionam para futuros SGX)
            fields = [
                "SETTLE",       # Preço de settlement (fechamento)
                "TRDPRC_1",     # Último preço negociado
                "BID",          # Bid
                "ASK",          # Ask
                "EXPIR_DATE",   # Data de vencimento
            ]

            logger.info(f"Buscando dados para {len(rics)} contratos: {rics}")

            # Busca dados
            response = ld.get_data(rics, fields=fields)

            if response is None or response.empty:
                logger.warning(f"Sem dados retornados para {rics}")
                return records

            now_utc = datetime.now(timezone.utc)

            for _, row in response.iterrows():
                ric = row.get("Instrument", "")
                # Usa TRDPRC_1 como preço principal, SETTLE como fallback
                last_price = row.get("TRDPRC_1")
                if pd.isna(last_price):
                    last_price = row.get("SETTLE")

                if pd.isna(last_price):
                    logger.warning(f"Preço inválido para {ric}")
                    continue

                # Extrai e formata expiry_date
                expiry_raw = row.get("EXPIR_DATE")
                expiry_date = None
                if not pd.isna(expiry_raw):
                    if isinstance(expiry_raw, pd.Timestamp):
                        expiry_date = expiry_raw.strftime("%Y-%m-%d")
                    elif isinstance(expiry_raw, str):
                        expiry_date = expiry_raw.split("T")[0]
                    else:
                        expiry_date = str(expiry_raw)

                # Calcula variable_key (prefere expiry_date, fallback para RIC)
                variable_key = expiry_date_to_variable_key(expiry_date)
                if not variable_key:
                    variable_key = ric_to_variable_key(ric)

                record = {
                    "timestamp": now_utc.isoformat(),
                    "source": "sgx",
                    "symbol": ric,
                    "price": float(last_price),
                    "variable_key": variable_key,
                    "expiry_date": expiry_date,
                    "price_type": "intraday",
                }

                # Settlement como close
                if not pd.isna(row.get("SETTLE")):
                    record["close"] = float(row.get("SETTLE"))
                    record["price_type"] = "settlement"

                records.append(record)
                logger.debug(f"Coletado: {ric} ({variable_key}) = {last_price}")

            logger.info(f"Coletados {len(records)} preços de minério (12 meses forward)")

        except Exception as e:
            logger.error(f"Erro ao buscar dados realtime: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_iron_ore",
                message=f"Erro ao buscar dados realtime: {e}",
            )
        finally:
            self._close_session()

        return records

    def fetch_historical(
        self,
        rics: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        interval: str = "daily",
    ) -> list[dict[str, Any]]:
        """
        Busca dados históricos de preços.

        Args:
            rics: Lista de RICs. Padrão: IRON_ORE_RICS (12 meses)
            start_date: Data início (YYYY-MM-DD). Padrão: 30 dias atrás
            end_date: Data fim (YYYY-MM-DD). Padrão: hoje
            interval: Intervalo (1H, 1D, etc.)

        Returns:
            Lista de dicts com dados históricos.
        """
        rics = rics or IRON_ORE_RICS
        records = []

        # Define datas padrão
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_dt = datetime.now() - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")

        try:
            if not self._open_session():
                return records

            # Primeiro busca expiry_date de cada RIC
            expiry_dates = {}
            try:
                expiry_response = ld.get_data(rics, fields=["EXPIR_DATE"])
                if expiry_response is not None and not expiry_response.empty:
                    for _, row in expiry_response.iterrows():
                        ric = row.get("Instrument", "")
                        expiry_raw = row.get("EXPIR_DATE")
                        if not pd.isna(expiry_raw):
                            if isinstance(expiry_raw, pd.Timestamp):
                                expiry_dates[ric] = expiry_raw.strftime("%Y-%m-%d")
                            elif isinstance(expiry_raw, str):
                                expiry_dates[ric] = expiry_raw.split("T")[0]
                            else:
                                expiry_dates[ric] = str(expiry_raw)
            except Exception as e:
                logger.warning(f"Não foi possível buscar expiry_dates: {e}")

            for ric in rics:
                logger.info(f"Buscando histórico {ric}: {start_date} a {end_date}")

                # Busca histórico
                response = ld.get_history(
                    universe=ric,
                    fields=["TRDPRC_1", "HIGH_1", "LOW_1", "OPEN_PRC", "ACVOL_UNS"],
                    interval=interval,
                    start=start_date,
                    end=end_date,
                )

                if response is None or response.empty:
                    logger.warning(f"Sem dados históricos para {ric}")
                    continue

                # Determina variable_key e expiry_date para este RIC
                expiry_date = expiry_dates.get(ric)
                variable_key = expiry_date_to_variable_key(expiry_date)
                if not variable_key:
                    variable_key = ric_to_variable_key(ric)

                count = 0
                for timestamp, row in response.iterrows():
                    price = row.get("TRDPRC_1")
                    if pd.isna(price):
                        continue

                    # Converte timestamp para UTC
                    if isinstance(timestamp, pd.Timestamp):
                        ts_utc = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
                    else:
                        ts_utc = pd.Timestamp(timestamp, tz="UTC")

                    record = {
                        "timestamp": ts_utc.isoformat(),
                        "source": "sgx",
                        "symbol": ric,
                        "price": float(price),
                        "variable_key": variable_key,
                        "expiry_date": expiry_date,
                        "price_type": "historical",
                    }

                    if not pd.isna(row.get("HIGH_1")):
                        record["high"] = float(row.get("HIGH_1"))
                    if not pd.isna(row.get("LOW_1")):
                        record["low"] = float(row.get("LOW_1"))
                    if not pd.isna(row.get("OPEN_PRC")):
                        record["open"] = float(row.get("OPEN_PRC"))
                    if not pd.isna(row.get("ACVOL_UNS")):
                        record["volume"] = int(row.get("ACVOL_UNS"))

                    records.append(record)
                    count += 1

                logger.info(f"Coletados {count} registros históricos para {ric} ({variable_key})")

        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos: {e}")
            self.supabase.log_system_event(
                level="error",
                component="fetch_iron_ore",
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
            return self.supabase.insert_iron_ore_prices(records)
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
            return self.supabase.insert_iron_ore_prices(records)
        return 0


def main() -> None:
    """Executa coleta de dados de minério de ferro."""
    import argparse

    parser = argparse.ArgumentParser(description="Coleta preços de minério de ferro")
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

    fetcher = IronOreFetcher()

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
