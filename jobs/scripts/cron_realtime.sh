#!/bin/bash
#
# Cron job para coleta de dados em tempo real
#
# Sugestão de agendamento (crontab):
#   # Minério SGX: a cada hora durante horário de mercado (20:25-17:45 BRT)
#   0 20-23,0-17 * * 1-5 /path/to/cron_realtime.sh
#
#   # VALE3: a cada hora durante horário B3 (10:00-17:55 BRT)
#   0 10-17 * * 1-5 /path/to/cron_realtime.sh
#

set -euo pipefail

# Diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Carrega variáveis de ambiente
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Ativa ambiente virtual se existir
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Define PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

# Log
LOG_FILE="$PROJECT_ROOT/jobs/logs/cron_realtime_$(date +%Y%m%d).log"

echo "========================================" >> "$LOG_FILE"
echo "Início: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# Executa coleta
cd "$PROJECT_ROOT"
python -m jobs.scripts.collect_all --mode realtime >> "$LOG_FILE" 2>&1

echo "Fim: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
