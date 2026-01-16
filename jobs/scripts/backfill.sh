#!/bin/bash
#
# Script para backfill de dados históricos
#
# Uso:
#   ./backfill.sh 2024-01-01           # De 2024-01-01 até hoje
#   ./backfill.sh 2024-01-01 2024-06-30  # Período específico
#

set -euo pipefail

# Diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Parâmetros
START_DATE="${1:-}"
END_DATE="${2:-$(date +%Y-%m-%d)}"

if [ -z "$START_DATE" ]; then
    echo "Uso: $0 <start-date> [end-date]"
    echo "Exemplo: $0 2024-01-01 2024-06-30"
    exit 1
fi

echo "Backfill de $START_DATE a $END_DATE"

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
LOG_FILE="$PROJECT_ROOT/jobs/logs/backfill_$(date +%Y%m%d_%H%M%S).log"

echo "Log: $LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "Backfill: $START_DATE a $END_DATE" >> "$LOG_FILE"
echo "Início: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# Executa backfill
cd "$PROJECT_ROOT"
python -m jobs.scripts.collect_all --mode historical --start-date "$START_DATE" --end-date "$END_DATE" 2>&1 | tee -a "$LOG_FILE"

echo "Fim: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo ""
echo "Backfill concluído! Log: $LOG_FILE"
