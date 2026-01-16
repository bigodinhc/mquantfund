"""
Cliente Supabase para persistência de dados do QuantFund.

Fornece métodos para inserir e consultar dados de preços,
sinais de trading e logs do sistema.
"""

from datetime import datetime
from typing import Any

from loguru import logger
from supabase import Client, create_client

from jobs.config.settings import (
    SUPABASE_KEY,
    SUPABASE_URL,
    TABLE_AUXILIARY_DATA,
    TABLE_IRON_ORE_PRICES,
    TABLE_SYSTEM_LOGS,
    TABLE_VALE3_PRICES,
)


class SupabaseClient:
    """Cliente para interação com Supabase."""

    def __init__(self) -> None:
        """Inicializa conexão com Supabase."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados")

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Conexão Supabase inicializada")

    def insert_iron_ore_prices(self, records: list[dict[str, Any]]) -> int:
        """
        Insere preços de minério de ferro.

        Args:
            records: Lista de dicts com campos conforme schema prices_iron_ore:
                - timestamp: datetime (UTC)
                - source: str ("sgx" ou "dce")
                - symbol: str (ex: "SZZFF6", "SZZFG6")
                - price: float
                - variable_key: str (ex: "DERIV_IO_SWAP_2026_01")
                - expiry_date: str (YYYY-MM-DD)
                - price_type: str ("intraday", "settlement", "historical")
                - volume: int (opcional)
                - open, high, low, close: float (opcional)

        Returns:
            Número de registros inseridos.
        """
        if not records:
            return 0

        # Mapeia campos para o schema do banco
        db_records = []
        for r in records:
            db_record = {
                "timestamp": r.get("timestamp"),
                "source": r.get("source", "sgx"),
                "symbol": r.get("symbol") or r.get("contract", "SGX_FE_62"),
                "price": r.get("price"),
            }

            # Campos de identificação de contrato futuro
            if r.get("variable_key"):
                db_record["variable_key"] = r["variable_key"]
            if r.get("expiry_date"):
                db_record["expiry_date"] = r["expiry_date"]
            if r.get("price_type"):
                db_record["price_type"] = r["price_type"]

            # Campos OHLCV opcionais
            if r.get("volume"):
                db_record["volume"] = r["volume"]
            if r.get("open"):
                db_record["open"] = r["open"]
            if r.get("high"):
                db_record["high"] = r["high"]
            if r.get("low"):
                db_record["low"] = r["low"]
            if r.get("close"):
                db_record["close"] = r["close"]

            db_records.append(db_record)

        try:
            # Usa variable_key para upsert (identifica contrato pelo vencimento)
            result = self.client.table(TABLE_IRON_ORE_PRICES).upsert(
                db_records, on_conflict="timestamp,source,variable_key"
            ).execute()
            count = len(result.data) if result.data else 0
            logger.info(f"Inseridos {count} registros em {TABLE_IRON_ORE_PRICES}")
            return count
        except Exception as e:
            logger.error(f"Erro ao inserir iron_ore_prices: {e}")
            raise

    def insert_vale3_prices(self, records: list[dict[str, Any]]) -> int:
        """
        Insere preços de VALE3.

        Args:
            records: Lista de dicts conforme schema prices_vale3:
                - timestamp: datetime (UTC)
                - open: float
                - high: float
                - low: float
                - close: float
                - volume: int

        Returns:
            Número de registros inseridos.
        """
        if not records:
            return 0

        # Adiciona campos padrão
        db_records = []
        for r in records:
            db_record = {
                "timestamp": r.get("timestamp"),
                "source": r.get("source", "lseg"),
                "symbol": r.get("symbol", "VALE3"),
                "open": r.get("open"),
                "high": r.get("high"),
                "low": r.get("low"),
                "close": r.get("close"),
                "volume": r.get("volume", 0),
            }
            db_records.append(db_record)

        try:
            result = self.client.table(TABLE_VALE3_PRICES).upsert(
                db_records, on_conflict="timestamp,source,symbol"
            ).execute()
            count = len(result.data) if result.data else 0
            logger.info(f"Inseridos {count} registros em {TABLE_VALE3_PRICES}")
            return count
        except Exception as e:
            logger.error(f"Erro ao inserir vale3_prices: {e}")
            raise

    def insert_auxiliary_data(self, records: list[dict[str, Any]]) -> int:
        """
        Insere dados auxiliares (USD/BRL, VIX).

        O schema auxiliary_data tem colunas separadas para cada indicador:
        - usd_brl: DECIMAL
        - vix: DECIMAL
        - ibov: DECIMAL (opcional)

        Args:
            records: Lista de dicts com campos:
                - timestamp: datetime (UTC)
                - indicator: str ("usd_brl" ou "vix")
                - value: float
                OU
                - usd_brl: float (direto)
                - vix: float (direto)

        Returns:
            Número de registros inseridos.
        """
        if not records:
            return 0

        # Agrupa por timestamp para consolidar usd_brl e vix no mesmo registro
        by_timestamp: dict[str, dict[str, Any]] = {}

        for r in records:
            ts = r.get("timestamp")
            if ts not in by_timestamp:
                by_timestamp[ts] = {"timestamp": ts}

            # Se usar formato indicator/value
            if "indicator" in r:
                indicator = r["indicator"]
                value = r["value"]
                by_timestamp[ts][indicator] = value
            else:
                # Formato direto
                if "usd_brl" in r:
                    by_timestamp[ts]["usd_brl"] = r["usd_brl"]
                if "vix" in r:
                    by_timestamp[ts]["vix"] = r["vix"]
                if "ibov" in r:
                    by_timestamp[ts]["ibov"] = r["ibov"]

        db_records = list(by_timestamp.values())

        try:
            result = self.client.table(TABLE_AUXILIARY_DATA).upsert(
                db_records, on_conflict="timestamp"
            ).execute()
            count = len(result.data) if result.data else 0
            logger.info(f"Inseridos {count} registros em {TABLE_AUXILIARY_DATA}")
            return count
        except Exception as e:
            logger.error(f"Erro ao inserir auxiliary_data: {e}")
            raise

    def log_system_event(
        self,
        level: str,
        component: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Registra evento no log do sistema.

        Args:
            level: Nível do log ("INFO", "WARNING", "ERROR", "CRITICAL")
            component: Componente que gerou o log (ex: "fetch_iron_ore")
            message: Mensagem do log
            details: Detalhes adicionais (opcional)
        """
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level.upper(),
                "component": component,
                "message": message,
                "details": details or {},
            }
            self.client.table(TABLE_SYSTEM_LOGS).insert(record).execute()
        except Exception as e:
            # Não propaga erro de log para não afetar operação principal
            logger.error(f"Erro ao registrar log no Supabase: {e}")

    def get_latest_iron_ore_price(
        self, source: str = "sgx", variable_key: str | None = None
    ) -> dict[str, Any] | None:
        """
        Obtém o preço mais recente de minério de ferro.

        Args:
            source: Fonte dos dados ("sgx" ou "dce")
            variable_key: Identificador do contrato (ex: "DERIV_IO_SWAP_2026_01")
                         Se None, retorna o front month (menor expiry_date)

        Returns:
            Dict com o registro mais recente ou None.
        """
        try:
            query = (
                self.client.table(TABLE_IRON_ORE_PRICES)
                .select("*")
                .eq("source", source)
            )

            if variable_key:
                query = query.eq("variable_key", variable_key)

            result = query.order("timestamp", desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Erro ao buscar latest iron_ore_price: {e}")
            return None

    def get_iron_ore_forward_curve(self, source: str = "sgx") -> list[dict[str, Any]]:
        """
        Obtém a curva forward completa de minério de ferro (12 meses).

        Args:
            source: Fonte dos dados ("sgx" ou "dce")

        Returns:
            Lista de dicts ordenados por expiry_date.
        """
        try:
            result = (
                self.client.table(TABLE_IRON_ORE_PRICES)
                .select("*")
                .eq("source", source)
                .not_.is_("variable_key", "null")
                .order("expiry_date", desc=False)
                .execute()
            )

            # Agrupa por variable_key e pega o mais recente de cada
            latest_by_key: dict[str, dict[str, Any]] = {}
            for row in result.data or []:
                key = row.get("variable_key")
                if key and (key not in latest_by_key or
                           row.get("timestamp", "") > latest_by_key[key].get("timestamp", "")):
                    latest_by_key[key] = row

            # Retorna ordenado por expiry_date
            return sorted(latest_by_key.values(), key=lambda x: x.get("expiry_date", ""))
        except Exception as e:
            logger.error(f"Erro ao buscar forward curve: {e}")
            return []

    def get_latest_vale3_price(self) -> dict[str, Any] | None:
        """
        Obtém o preço mais recente de VALE3.

        Returns:
            Dict com o registro mais recente ou None.
        """
        try:
            result = (
                self.client.table(TABLE_VALE3_PRICES)
                .select("*")
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Erro ao buscar latest vale3_price: {e}")
            return None

    def get_latest_auxiliary(self) -> dict[str, Any] | None:
        """
        Obtém os valores mais recentes de USD/BRL e VIX.

        Returns:
            Dict com timestamp, usd_brl e vix ou None.
        """
        try:
            result = (
                self.client.table(TABLE_AUXILIARY_DATA)
                .select("*")
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Erro ao buscar latest auxiliary: {e}")
            return None


# Singleton para uso em todo o projeto
_client: SupabaseClient | None = None


def get_supabase_client() -> SupabaseClient:
    """Retorna instância singleton do cliente Supabase."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
