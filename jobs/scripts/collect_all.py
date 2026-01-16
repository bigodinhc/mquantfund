#!/usr/bin/env python3
"""
Script principal de coleta de dados.

Coleta todos os dados necessários para a estratégia:
- Minério de ferro SGX
- VALE3
- USD/BRL
- VIX

Uso:
    python collect_all.py --mode realtime
    python collect_all.py --mode historical --start-date 2024-01-01
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger

from jobs.ingestion.fetch_auxiliary import AuxiliaryFetcher
from jobs.ingestion.fetch_iron_ore import IronOreFetcher
from jobs.ingestion.fetch_vale3 import Vale3Fetcher


def collect_realtime() -> dict[str, int]:
    """
    Coleta dados em tempo real de todas as fontes.

    Returns:
        Dict com contagem de registros por fonte.
    """
    results = {}

    logger.info("Iniciando coleta realtime...")

    # Minério de ferro
    try:
        fetcher = IronOreFetcher()
        results["iron_ore"] = fetcher.fetch_and_persist_realtime()
        logger.info(f"Minério: {results['iron_ore']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar minério: {e}")
        results["iron_ore"] = 0

    # VALE3
    try:
        fetcher = Vale3Fetcher()
        results["vale3"] = fetcher.fetch_and_persist_realtime()
        logger.info(f"VALE3: {results['vale3']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar VALE3: {e}")
        results["vale3"] = 0

    # Auxiliares (USD/BRL, VIX)
    try:
        fetcher = AuxiliaryFetcher()
        results["auxiliary"] = fetcher.fetch_and_persist_realtime()
        logger.info(f"Auxiliares: {results['auxiliary']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar auxiliares: {e}")
        results["auxiliary"] = 0

    total = sum(results.values())
    logger.info(f"Coleta realtime concluída: {total} registros total")

    return results


def collect_historical(start_date: str, end_date: str | None = None) -> dict[str, int]:
    """
    Coleta dados históricos de todas as fontes.

    Args:
        start_date: Data início (YYYY-MM-DD)
        end_date: Data fim (YYYY-MM-DD). Padrão: hoje

    Returns:
        Dict com contagem de registros por fonte.
    """
    results = {}

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Iniciando coleta histórica: {start_date} a {end_date}")

    # Minério de ferro
    try:
        fetcher = IronOreFetcher()
        results["iron_ore"] = fetcher.fetch_and_persist_historical(
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Minério: {results['iron_ore']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar minério histórico: {e}")
        results["iron_ore"] = 0

    # VALE3
    try:
        fetcher = Vale3Fetcher()
        results["vale3"] = fetcher.fetch_and_persist_historical(
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"VALE3: {results['vale3']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar VALE3 histórico: {e}")
        results["vale3"] = 0

    # Auxiliares (USD/BRL, VIX)
    try:
        fetcher = AuxiliaryFetcher()
        results["auxiliary"] = fetcher.fetch_and_persist_historical(
            start_date=start_date,
            end_date=end_date,
        )
        logger.info(f"Auxiliares: {results['auxiliary']} registros")
    except Exception as e:
        logger.error(f"Erro ao coletar auxiliares histórico: {e}")
        results["auxiliary"] = 0

    total = sum(results.values())
    logger.info(f"Coleta histórica concluída: {total} registros total")

    return results


def main() -> None:
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Coleta dados de mercado para estratégia QuantFund"
    )
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

    if args.mode == "realtime":
        collect_realtime()
    elif args.mode in ("historical", "backfill"):
        if not args.start_date:
            logger.error("--start-date é obrigatório para modo histórico")
            sys.exit(1)
        collect_historical(args.start_date, args.end_date)


if __name__ == "__main__":
    main()
