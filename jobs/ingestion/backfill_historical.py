"""
Backfill de dados históricos longos (5+ anos).

Usa Yahoo Finance para dados históricos de longo prazo:
- Minério de ferro (TIO=F)
- VALE3 (VALE3.SA)
- USD/BRL (BRL=X)
- VIX (^VIX)
- IBOV (^BVSP)

Os dados do LSEG são usados para dados recentes/realtime.
Yahoo Finance é usado para backfill histórico (gratuito, 7+ anos).

Uso:
    python -m jobs.ingestion.backfill_historical --years 5
    python -m jobs.ingestion.backfill_historical --years 7 --type all
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf
from loguru import logger

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jobs.clients.supabase_client import get_supabase_client


# Mapeamento de tickers Yahoo Finance
YAHOO_TICKERS = {
    "iron_ore": "TIO=F",      # SGX Iron Ore 62% Fe
    "vale3": "VALE3.SA",       # VALE3 na B3
    "usd_brl": "BRL=X",        # USD/BRL
    "vix": "^VIX",             # VIX
    "ibov": "^BVSP",           # Ibovespa
}


def download_yahoo_data(
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Baixa dados históricos do Yahoo Finance.

    Args:
        ticker: Ticker do Yahoo Finance
        start_date: Data início (YYYY-MM-DD)
        end_date: Data fim (YYYY-MM-DD)

    Returns:
        DataFrame com dados OHLCV
    """
    logger.info(f"Baixando {ticker}: {start_date} a {end_date}")

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        progress=False,
        auto_adjust=True,  # Ajusta para splits/dividendos
    )

    if data.empty:
        logger.warning(f"Sem dados para {ticker}")
        return pd.DataFrame()

    # Flatten multi-index columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    logger.info(f"{ticker}: {len(data)} registros baixados")
    return data


def backfill_iron_ore(years: int = 5) -> int:
    """
    Backfill de preços de minério de ferro via LSEG (SGX).

    Usa SZZFc1 (contrato contínuo front month da SGX Cingapura).

    Args:
        years: Número de anos para buscar

    Returns:
        Número de registros inseridos
    """
    logger.info(f"Iniciando backfill de minério de ferro SGX ({years} anos)")

    # Importa LSEG
    try:
        import lseg.data as ld
        from jobs.config.settings import LSEG_CONFIG_PATH
    except ImportError:
        logger.error("lseg-data não instalado")
        return 0

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")

    records = []

    try:
        # Abre sessão LSEG
        ld.open_session(config_name=str(LSEG_CONFIG_PATH))
        logger.info("Sessão LSEG aberta")

        # Busca histórico do contrato contínuo SGX
        response = ld.get_history(
            universe="SZZFc2",  # SGX front month contínuo
            interval="daily",
            start=start_date,
            end=end_date,
        )

        if response is None or response.empty:
            logger.warning("Sem dados retornados do LSEG")
            return 0

        logger.info(f"Baixados {len(response)} registros do LSEG")

        for timestamp, row in response.iterrows():
            ts = pd.Timestamp(timestamp)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")

            # Usa SETTLE como preço (campo principal para futuros)
            price = row.get("SETTLE")
            if pd.isna(price):
                continue

            record = {
                "timestamp": ts.isoformat(),
                "source": "sgx",
                "symbol": "SZZFc2",
                "price": float(price),
                "variable_key": "SGX_IO_62_FE_FRONT",
                "price_type": "settlement",
                "close": float(price),
            }

            records.append(record)

    except Exception as e:
        logger.error(f"Erro ao buscar dados LSEG: {e}")
    finally:
        try:
            ld.close_session()
            logger.info("Sessão LSEG fechada")
        except Exception:
            pass

    if records:
        client = get_supabase_client()
        count = client.insert_iron_ore_prices(records)
        logger.info(f"Minério de ferro SGX: {count} registros inseridos")
        return count

    return 0


def backfill_vale3(years: int = 5) -> int:
    """
    Backfill de preços de VALE3.

    Args:
        years: Número de anos para buscar

    Returns:
        Número de registros inseridos
    """
    logger.info(f"Iniciando backfill de VALE3 ({years} anos)")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")

    data = download_yahoo_data(YAHOO_TICKERS["vale3"], start_date, end_date)

    if data.empty:
        return 0

    records = []
    for timestamp, row in data.iterrows():
        ts = pd.Timestamp(timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")

        record = {
            "timestamp": ts.isoformat(),
            "source": "yahoo",
            "symbol": "VALE3",
            "close": float(row["Close"]),
        }

        if not pd.isna(row.get("Open")):
            record["open"] = float(row["Open"])
        if not pd.isna(row.get("High")):
            record["high"] = float(row["High"])
        if not pd.isna(row.get("Low")):
            record["low"] = float(row["Low"])
        if not pd.isna(row.get("Volume")) and row["Volume"] > 0:
            record["volume"] = int(row["Volume"])

        records.append(record)

    if records:
        client = get_supabase_client()
        count = client.insert_vale3_prices(records)
        logger.info(f"VALE3: {count} registros inseridos")
        return count

    return 0


def backfill_auxiliary(years: int = 5) -> int:
    """
    Backfill de dados auxiliares (USD/BRL, VIX, IBOV).

    Args:
        years: Número de anos para buscar

    Returns:
        Número de registros inseridos
    """
    logger.info(f"Iniciando backfill de dados auxiliares ({years} anos)")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")

    # Baixa todos os dados
    data_frames = {}
    for name in ["usd_brl", "vix", "ibov"]:
        ticker = YAHOO_TICKERS[name]
        data = download_yahoo_data(ticker, start_date, end_date)
        if not data.empty:
            data_frames[name] = data["Close"]

    if not data_frames:
        return 0

    # Combina em um DataFrame
    combined = pd.DataFrame(data_frames)

    records = []
    for timestamp, row in combined.iterrows():
        ts = pd.Timestamp(timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")

        record = {"timestamp": ts.isoformat()}

        if not pd.isna(row.get("usd_brl")):
            record["usd_brl"] = float(row["usd_brl"])
        if not pd.isna(row.get("vix")):
            record["vix"] = float(row["vix"])
        if not pd.isna(row.get("ibov")):
            record["ibov"] = float(row["ibov"])

        # Só adiciona se tiver pelo menos um valor
        if len(record) > 1:
            records.append(record)

    if records:
        client = get_supabase_client()
        count = client.insert_auxiliary_data(records)
        logger.info(f"Dados auxiliares: {count} registros inseridos")
        return count

    return 0


def normalize_dataframe(
    df: pd.DataFrame,
    method: str = "ffill",
    reference_col: str | None = None,
) -> pd.DataFrame:
    """
    Normaliza DataFrame para alinhar datas entre diferentes mercados.

    Args:
        df: DataFrame com index de datas
        method: Método de normalização:
            - "ffill": Forward fill (repete último valor)
            - "bfill": Backward fill
            - "interpolate": Interpolação linear
            - "dropna": Remove linhas com NaN (inner join)
        reference_col: Coluna de referência para filtrar dias válidos

    Returns:
        DataFrame normalizado
    """
    df = df.copy()

    if method == "ffill":
        df = df.ffill()
    elif method == "bfill":
        df = df.bfill()
    elif method == "interpolate":
        df = df.interpolate(method="linear")
    elif method == "dropna":
        df = df.dropna()

    # Se tiver coluna de referência, filtra apenas dias onde ela existe
    if reference_col and reference_col in df.columns:
        df = df[df[reference_col].notna()]

    return df


def create_aligned_dataset(years: int = 5) -> pd.DataFrame:
    """
    Cria dataset alinhado com todos os dados normalizados.

    Estratégia:
    1. Baixa todos os dados
    2. Cria DataFrame com todas as datas
    3. Forward fill para preencher gaps
    4. Filtra apenas dias onde VALE3 tem dados (mercado BR aberto)

    Args:
        years: Número de anos

    Returns:
        DataFrame alinhado e normalizado
    """
    logger.info(f"Criando dataset alinhado ({years} anos)")

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")

    # Baixa todos os dados
    iron = download_yahoo_data(YAHOO_TICKERS["iron_ore"], start_date, end_date)
    vale = download_yahoo_data(YAHOO_TICKERS["vale3"], start_date, end_date)
    usd = download_yahoo_data(YAHOO_TICKERS["usd_brl"], start_date, end_date)
    vix = download_yahoo_data(YAHOO_TICKERS["vix"], start_date, end_date)

    # Cria DataFrame combinado
    df = pd.DataFrame({
        "iron_ore": iron["Close"] if not iron.empty else None,
        "vale3": vale["Close"] if not vale.empty else None,
        "usd_brl": usd["Close"] if not usd.empty else None,
        "vix": vix["Close"] if not vix.empty else None,
    })

    # Forward fill para preencher gaps (mercados fechados)
    df = df.ffill()

    # Filtra apenas dias onde VALE3 tem dados (B3 aberta)
    df = df[df["vale3"].notna()]

    # Calcula retornos
    df["iron_return"] = df["iron_ore"].pct_change() * 100
    df["vale3_return"] = df["vale3"].pct_change() * 100

    logger.info(f"Dataset alinhado: {len(df)} registros")
    logger.info(f"Período: {df.index.min()} a {df.index.max()}")

    return df


def main() -> None:
    """Entry point para backfill histórico."""
    parser = argparse.ArgumentParser(description="Backfill de dados históricos longos")
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Número de anos para backfill (default: 5)",
    )
    parser.add_argument(
        "--type",
        choices=["all", "iron-ore", "vale3", "auxiliary"],
        default="all",
        help="Tipo de dados para backfill",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Apenas analisa dados sem inserir no banco",
    )

    args = parser.parse_args()

    if args.analyze:
        # Modo análise: cria dataset alinhado e mostra estatísticas
        df = create_aligned_dataset(args.years)
        print("\n" + "=" * 60)
        print("DATASET ALINHADO")
        print("=" * 60)
        print(f"\nPeríodo: {df.index.min().date()} a {df.index.max().date()}")
        print(f"Observações: {len(df)}")
        print("\nEstatísticas:")
        print(df.describe())
        print("\nCorrelação de retornos:")
        print(f"  Iron Ore x VALE3: {df['iron_return'].corr(df['vale3_return']):.4f}")
        print("\nDados faltantes por coluna:")
        print(df.isna().sum())
        return

    logger.info(f"Iniciando backfill: {args.years} anos, tipo={args.type}")

    total_records = 0

    if args.type in ("all", "iron-ore"):
        total_records += backfill_iron_ore(args.years)

    if args.type in ("all", "vale3"):
        total_records += backfill_vale3(args.years)

    if args.type in ("all", "auxiliary"):
        total_records += backfill_auxiliary(args.years)

    logger.info(f"Backfill finalizado: {total_records} registros totais")


if __name__ == "__main__":
    main()
