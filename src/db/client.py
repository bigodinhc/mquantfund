"""
Cliente Supabase para o sistema QuantFund.
Gerencia conexão e operações com o banco de dados.
"""

from datetime import datetime
from typing import Any

from loguru import logger
from supabase import Client, create_client

from src.config import SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL


class SupabaseClient:
    """Cliente singleton para conexão com Supabase."""

    _instance: Client | None = None

    @classmethod
    def get_client(cls, use_service_key: bool = False) -> Client:
        """
        Retorna instância do cliente Supabase.

        Args:
            use_service_key: Se True, usa service key (backend).
                            Se False, usa anon key (frontend/público).

        Returns:
            Cliente Supabase configurado.
        """
        if cls._instance is None:
            key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_ANON_KEY
            if not SUPABASE_URL or not key:
                raise ValueError(
                    "SUPABASE_URL e SUPABASE_KEY devem estar configurados no .env"
                )
            cls._instance = create_client(SUPABASE_URL, key)
            logger.info("Cliente Supabase inicializado")
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reseta a instância (útil para testes)."""
        cls._instance = None


# Funções de conveniência para operações comuns
def get_supabase() -> Client:
    """Retorna cliente Supabase com service key."""
    return SupabaseClient.get_client(use_service_key=True)


# -------------------------------------------
# Operações de Preços - Minério
# -------------------------------------------
def save_iron_ore_price(
    timestamp: datetime,
    source: str,
    symbol: str,
    price: float,
    volume: int | None = None,
    ohlc: dict[str, float] | None = None,
) -> dict[str, Any] | None:
    """
    Salva preço de minério de ferro no banco.

    Args:
        timestamp: Momento do preço
        source: Fonte dos dados ('yahoo', 'investing', etc.)
        symbol: Símbolo ('SGX_FE_62', 'DCE_IO', etc.)
        price: Preço atual
        volume: Volume negociado (opcional)
        ohlc: Dict com open, high, low, close (opcional)

    Returns:
        Registro inserido ou None se erro.
    """
    client = get_supabase()

    data = {
        "timestamp": timestamp.isoformat(),
        "source": source,
        "symbol": symbol,
        "price": price,
        "volume": volume,
    }

    if ohlc:
        data.update({
            "open": ohlc.get("open"),
            "high": ohlc.get("high"),
            "low": ohlc.get("low"),
            "close": ohlc.get("close"),
        })

    try:
        result = client.table("prices_iron_ore").upsert(data).execute()
        logger.debug(f"Preço minério salvo: {source}/{symbol} = {price}")
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Erro ao salvar preço minério: {e}")
        return None


def get_iron_ore_prices(
    limit: int = 100,
    source: str | None = None,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Busca preços de minério de ferro.

    Args:
        limit: Número máximo de registros
        source: Filtrar por fonte (opcional)
        since: Buscar desde esta data (opcional)

    Returns:
        Lista de registros de preços.
    """
    client = get_supabase()
    query = client.table("prices_iron_ore").select("*")

    if source:
        query = query.eq("source", source)
    if since:
        query = query.gte("timestamp", since.isoformat())

    query = query.order("timestamp", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Erro ao buscar preços minério: {e}")
        return []


# -------------------------------------------
# Operações de Preços - VALE3
# -------------------------------------------
def save_vale_price(
    timestamp: datetime,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: int,
    source: str = "mt5",
    tick_volume: int | None = None,
    spread: int | None = None,
) -> dict[str, Any] | None:
    """
    Salva preço de VALE3 no banco.

    Args:
        timestamp: Momento do preço
        open_price: Preço de abertura
        high: Máxima
        low: Mínima
        close: Fechamento
        volume: Volume
        source: Fonte dos dados
        tick_volume: Volume de ticks (MT5)
        spread: Spread (MT5)

    Returns:
        Registro inserido ou None se erro.
    """
    client = get_supabase()

    data = {
        "timestamp": timestamp.isoformat(),
        "source": source,
        "symbol": "VALE3",
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "tick_volume": tick_volume,
        "spread": spread,
    }

    try:
        result = client.table("prices_vale3").upsert(data).execute()
        logger.debug(f"Preço VALE3 salvo: {close} @ {timestamp}")
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Erro ao salvar preço VALE3: {e}")
        return None


def get_vale_prices(
    limit: int = 100,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Busca preços de VALE3.

    Args:
        limit: Número máximo de registros
        since: Buscar desde esta data (opcional)

    Returns:
        Lista de registros de preços.
    """
    client = get_supabase()
    query = client.table("prices_vale3").select("*")

    if since:
        query = query.gte("timestamp", since.isoformat())

    query = query.order("timestamp", desc=True).limit(limit)

    try:
        result = query.execute()
        return result.data or []
    except Exception as e:
        logger.error(f"Erro ao buscar preços VALE3: {e}")
        return []


# -------------------------------------------
# Operações de Dados Auxiliares
# -------------------------------------------
def save_auxiliary_data(
    timestamp: datetime,
    usd_brl: float | None = None,
    vix: float | None = None,
    ibov: float | None = None,
) -> dict[str, Any] | None:
    """Salva dados auxiliares (USD/BRL, VIX, IBOV)."""
    client = get_supabase()

    data = {
        "timestamp": timestamp.isoformat(),
        "usd_brl": usd_brl,
        "vix": vix,
        "ibov": ibov,
    }

    try:
        result = client.table("auxiliary_data").upsert(data).execute()
        logger.debug(f"Dados auxiliares salvos: USD/BRL={usd_brl}, VIX={vix}")
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Erro ao salvar dados auxiliares: {e}")
        return None


# -------------------------------------------
# Operações de Sinais
# -------------------------------------------
def save_signal(
    timestamp: datetime,
    signal_type: str,
    confidence: float,
    iron_ore_return: float,
    iron_ore_zscore: float,
    features: dict[str, Any] | None = None,
    strategy: str = "rule_based",
) -> dict[str, Any] | None:
    """Salva sinal gerado pelo sistema."""
    client = get_supabase()

    data = {
        "timestamp": timestamp.isoformat(),
        "signal_type": signal_type,
        "symbol": "VALE3",
        "confidence": confidence,
        "iron_ore_return": iron_ore_return,
        "iron_ore_zscore": iron_ore_zscore,
        "features_json": features,
        "strategy": strategy,
        "executed": False,
    }

    try:
        result = client.table("signals").insert(data).execute()
        logger.info(f"Sinal salvo: {signal_type} (confiança={confidence:.2%})")
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Erro ao salvar sinal: {e}")
        return None


# -------------------------------------------
# Teste de Conexão
# -------------------------------------------
def test_connection() -> bool:
    """Testa conexão com Supabase."""
    try:
        client = get_supabase()
        # Tenta uma operação simples
        result = client.table("prices_iron_ore").select("id").limit(1).execute()
        logger.info("Conexão com Supabase OK")
        return True
    except Exception as e:
        logger.error(f"Erro de conexão com Supabase: {e}")
        return False


if __name__ == "__main__":
    # Testar conexão
    print("Testando conexão com Supabase...")
    if test_connection():
        print("✓ Conexão OK!")
    else:
        print("✗ Falha na conexão. Verifique as credenciais no .env")
