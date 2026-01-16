"""
Configurações centralizadas do QuantFund.

Carrega variáveis de ambiente do arquivo .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega .env do diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# =============================================================================
# LSEG Workspace
# =============================================================================
LSEG_APP_KEY = os.getenv("LSEG_APP_KEY", "")
LSEG_USERNAME = os.getenv("LSEG_USERNAME", "")
LSEG_PASSWORD = os.getenv("LSEG_PASSWORD", "")

# =============================================================================
# Supabase
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# =============================================================================
# Telegram (para alertas)
# =============================================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# =============================================================================
# Instrumentos
# =============================================================================

# Minério de ferro SGX - 62% Fe CFR China
# RICs são gerados dinamicamente: SZZF + código do mês + último dígito do ano
# Mapeamento de meses para código RIC
MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}

def generate_iron_ore_rics(num_months: int = 3) -> list[str]:
    """Gera RICs para os próximos N meses de contratos futuros de minério."""
    from datetime import date
    from dateutil.relativedelta import relativedelta

    rics = []
    today = date.today()
    for i in range(num_months):
        target_date = today + relativedelta(months=i)
        year_code = str(target_date.year)[-1]
        month_code = MONTH_CODES[target_date.month]
        ric = f"SZZF{month_code}{year_code}"
        rics.append(ric)
    return rics

# RICs padrão (12 meses forward para curva completa)
IRON_ORE_RICS = generate_iron_ore_rics(12)


def expiry_date_to_variable_key(expiry_date: str | None) -> str | None:
    """
    Converte data de vencimento para variable_key no formato DERIV_IO_SWAP_YYYY_MM.

    Args:
        expiry_date: Data de vencimento no formato YYYY-MM-DD ou similar

    Returns:
        Variable key no formato DERIV_IO_SWAP_YYYY_MM ou None se inválido
    """
    if not expiry_date:
        return None

    try:
        from datetime import datetime

        # Tenta parsear diferentes formatos
        if isinstance(expiry_date, str):
            # Remove possível timezone
            clean_date = expiry_date.split("T")[0].split(" ")[0]
            dt = datetime.strptime(clean_date, "%Y-%m-%d")
        else:
            dt = expiry_date

        return f"DERIV_IO_SWAP_{dt.year}_{dt.month:02d}"
    except (ValueError, AttributeError):
        return None


def ric_to_variable_key(ric: str) -> str | None:
    """
    Converte RIC para variable_key baseado no código do mês e ano.

    Args:
        ric: RIC no formato SZZFXY (X=mês, Y=ano)

    Returns:
        Variable key no formato DERIV_IO_SWAP_YYYY_MM ou None se inválido
    """
    if not ric or len(ric) < 6 or not ric.startswith("SZZF"):
        return None

    try:
        from datetime import date

        # Extrai código do mês e ano do RIC
        month_code = ric[4]
        year_digit = ric[5]

        # Inverte o dicionário de meses
        code_to_month = {v: k for k, v in MONTH_CODES.items()}

        if month_code not in code_to_month:
            return None

        month = code_to_month[month_code]

        # Calcula o ano completo (assume próxima década se necessário)
        current_year = date.today().year
        current_decade = (current_year // 10) * 10
        year = current_decade + int(year_digit)

        # Se o ano calculado for muito no passado, ajusta para próxima década
        if year < current_year - 1:
            year += 10

        return f"DERIV_IO_SWAP_{year}_{month:02d}"
    except (ValueError, IndexError):
        return None

# VALE3 na B3
VALE3_RIC = "VALE3.SA"

# Auxiliares
USDBRL_RIC = "BRL="
VIX_RIC = ".VIX"

# =============================================================================
# Tabelas Supabase (conforme 001_initial_schema.sql)
# =============================================================================
TABLE_IRON_ORE_PRICES = "prices_iron_ore"
TABLE_VALE3_PRICES = "prices_vale3"
TABLE_AUXILIARY_DATA = "auxiliary_data"
TABLE_SIGNALS = "signals"
TABLE_ORDERS = "orders"
TABLE_POSITIONS = "positions"
TABLE_DAILY_METRICS = "daily_metrics"
TABLE_SYSTEM_LOGS = "system_logs"
TABLE_KILL_SWITCH_EVENTS = "kill_switch_events"

# =============================================================================
# Caminhos
# =============================================================================
LOGS_DIR = PROJECT_ROOT / "jobs" / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Config LSEG
LSEG_CONFIG_PATH = PROJECT_ROOT / "jobs" / "lseg-data.config.json"


def validate_config() -> dict[str, bool]:
    """Valida se as configurações essenciais estão presentes."""
    return {
        "lseg": bool(LSEG_APP_KEY and LSEG_USERNAME and LSEG_PASSWORD),
        "supabase": bool(SUPABASE_URL and SUPABASE_KEY),
        "telegram": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
    }


if __name__ == "__main__":
    print("Validação de configuração:")
    for key, valid in validate_config().items():
        status = "✓" if valid else "✗"
        print(f"  {status} {key}")
