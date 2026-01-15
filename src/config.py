"""
Configuração central do sistema QuantFund.
Carrega variáveis de ambiente e define constantes.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# -------------------------------------------
# Paths
# -------------------------------------------
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Criar diretórios se não existirem
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# -------------------------------------------
# Supabase
# -------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# -------------------------------------------
# MetaTrader 5
# -------------------------------------------
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "Clear-Demo")

# -------------------------------------------
# Telegram
# -------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# -------------------------------------------
# Trading Parameters
# -------------------------------------------
CAPITAL = float(os.getenv("CAPITAL", "50000"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))
MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "0.20"))
DAILY_LOSS_LIMIT = float(os.getenv("DAILY_LOSS_LIMIT", "0.025"))
WEEKLY_LOSS_LIMIT = float(os.getenv("WEEKLY_LOSS_LIMIT", "0.05"))
MONTHLY_LOSS_LIMIT = float(os.getenv("MONTHLY_LOSS_LIMIT", "0.10"))
MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.20"))

# -------------------------------------------
# Environment
# -------------------------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# -------------------------------------------
# Trading Hours (UTC)
# -------------------------------------------
# DCE: 01:00-07:00 UTC (22:00-04:00 BRT D-1)
# SGX T-Session: 23:25(D-1)-12:00 UTC (20:25-09:00 BRT)
# B3: 13:00-20:55 UTC (10:00-17:55 BRT)

MARKET_HOURS = {
    "DCE": {"open": "01:00", "close": "07:00", "timezone": "UTC"},
    "SGX": {"open": "23:25", "close": "12:00", "timezone": "UTC"},  # T-Session
    "B3": {"open": "13:00", "close": "20:55", "timezone": "UTC"},
}

# Janela crítica: SGX fecha 12:00 UTC, B3 abre 13:00 UTC (1h gap)
CRITICAL_WINDOW_START = "12:00"  # UTC - SGX fecha
CRITICAL_WINDOW_END = "13:00"  # UTC - B3 abre

# -------------------------------------------
# Strategy Parameters
# -------------------------------------------
SIGNAL_THRESHOLD_STD = 1.5  # Desvios padrão para sinal
ROLLING_WINDOW = 20  # Dias para cálculo de volatilidade
CORRELATION_THRESHOLD = 0.2  # Mínimo para continuar operando
ATR_PERIOD = 14  # Período do ATR
STOP_MULTIPLIER = 2.0  # Stop = 2x ATR

# -------------------------------------------
# Data Sources
# -------------------------------------------
IRON_ORE_SYMBOLS = {
    "yahoo": "SGX=F",  # Verificar ticker correto
    "investing": "iron-ore-62-cfr-futures",
}

VALE_SYMBOL = "VALE3"

# -------------------------------------------
# Validation
# -------------------------------------------
def validate_config() -> list[str]:
    """Valida se todas as configurações necessárias estão presentes."""
    errors = []

    if not SUPABASE_URL:
        errors.append("SUPABASE_URL não configurado")
    if not SUPABASE_ANON_KEY:
        errors.append("SUPABASE_ANON_KEY não configurado")

    if ENVIRONMENT == "production":
        if not MT5_LOGIN:
            errors.append("MT5_LOGIN não configurado")
        if not MT5_PASSWORD:
            errors.append("MT5_PASSWORD não configurado")
        if not TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN não configurado")
        if not TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID não configurado")

    return errors


if __name__ == "__main__":
    # Testar configuração
    errors = validate_config()
    if errors:
        print("Erros de configuração:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("Configuração OK!")
        print(f"Environment: {ENVIRONMENT}")
        print(f"Capital: R${CAPITAL:,.2f}")
        print(f"Supabase URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "Supabase: Não configurado")
