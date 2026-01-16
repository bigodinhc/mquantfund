# Arquitetura e Fluxo de Dados - QuantFund

Este documento descreve a arquitetura completa do sistema QuantFund, incluindo coleta, armazenamento e processamento de dados.

---

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FONTES DE DADOS                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │ Yahoo Finance│    │    LSEG      │    │   Investing  │    │     B3       │  │
│   │   (Backup)   │    │  (Realtime)  │    │   (Backup)   │    │  (via MT5)   │  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│          │                   │                   │                   │          │
│          │   Iron Ore        │   Iron Ore        │   Iron Ore        │  VALE3   │
│          │   USD/BRL         │   Forward Curve   │                   │  OHLCV   │
│          │   VIX, IBOV       │   VALE3           │                   │          │
│          │                   │   USD/BRL, VIX    │                   │          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CAMADA DE COLETA                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────┐    ┌─────────────────────────────────┐   │
│   │     src/data/backfill.py        │    │   jobs/ingestion/fetch_*.py     │   │
│   │                                 │    │                                 │   │
│   │  • backfill_iron_ore()          │    │  • IronOreFetcher (LSEG)        │   │
│   │  • backfill_vale3()             │    │  • Vale3Fetcher (LSEG)          │   │
│   │  • backfill_auxiliary()         │    │  • AuxiliaryFetcher (LSEG)      │   │
│   │                                 │    │                                 │   │
│   │  Fonte: Yahoo Finance           │    │  Fonte: LSEG Workspace API      │   │
│   │  Uso: Backfill histórico        │    │  Uso: Coleta real-time          │   │
│   └─────────────────────────────────┘    └─────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CAMADA DE PERSISTÊNCIA                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        src/db/client.py                                  │   │
│   │                                                                          │   │
│   │   SupabaseClient (Singleton)                                             │   │
│   │   ├── save_iron_ore_price()  → prices_iron_ore                          │   │
│   │   ├── save_vale_price()      → prices_vale3                             │   │
│   │   ├── save_auxiliary_data()  → auxiliary_data                           │   │
│   │   ├── save_signal()          → signals                                  │   │
│   │   ├── get_iron_ore_prices()  ← prices_iron_ore                          │   │
│   │   ├── get_vale_prices()      ← prices_vale3                             │   │
│   │   └── test_connection()      → health check                             │   │
│   │                                                                          │   │
│   │   Método: UPSERT (insert or update on conflict)                         │   │
│   │   Conexão: Service Key (backend)                                         │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SUPABASE                                            │
│                         PostgreSQL Gerenciado                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│   │ prices_iron_ore │  │   prices_vale3  │  │ auxiliary_data  │                │
│   ├─────────────────┤  ├─────────────────┤  ├─────────────────┤                │
│   │ id              │  │ id              │  │ id              │                │
│   │ timestamp       │  │ timestamp       │  │ timestamp       │                │
│   │ source          │  │ source          │  │ usd_brl         │                │
│   │ symbol          │  │ symbol          │  │ vix             │                │
│   │ price           │  │ open            │  │ ibov            │                │
│   │ volume          │  │ high            │  │ created_at      │                │
│   │ open            │  │ low             │  └─────────────────┘                │
│   │ high            │  │ close           │                                      │
│   │ low             │  │ volume          │  ┌─────────────────┐                │
│   │ close           │  │ tick_volume     │  │     signals     │                │
│   │ created_at      │  │ spread          │  ├─────────────────┤                │
│   └─────────────────┘  │ created_at      │  │ id              │                │
│                        └─────────────────┘  │ timestamp       │                │
│                                             │ signal_type     │                │
│   ┌─────────────────┐  ┌─────────────────┐  │ symbol          │                │
│   │     orders      │  │    positions    │  │ confidence      │                │
│   ├─────────────────┤  ├─────────────────┤  │ iron_ore_return │                │
│   │ id              │  │ id              │  │ iron_ore_zscore │                │
│   │ timestamp       │  │ symbol          │  │ features_json   │                │
│   │ order_id        │  │ side            │  │ strategy        │                │
│   │ signal_id (FK)  │  │ quantity        │  │ executed        │                │
│   │ symbol          │  │ entry_price     │  │ created_at      │                │
│   │ side            │  │ exit_price      │  └─────────────────┘                │
│   │ order_type      │  │ realized_pnl    │                                      │
│   │ quantity        │  │ status          │  ┌─────────────────┐                │
│   │ price           │  │ stop_loss       │  │  daily_metrics  │                │
│   │ status          │  │ take_profit     │  ├─────────────────┤                │
│   │ fill_price      │  │ exit_reason     │  │ date            │                │
│   │ slippage_bps    │  │ created_at      │  │ daily_pnl       │                │
│   │ commission      │  │ updated_at      │  │ daily_return    │                │
│   └─────────────────┘  └─────────────────┘  │ sharpe_ratio    │                │
│                                             │ max_drawdown    │                │
│   ┌─────────────────┐  ┌─────────────────┐  │ correlation     │                │
│   │   system_logs   │  │ kill_switch_evt │  └─────────────────┘                │
│   ├─────────────────┤  ├─────────────────┤                                      │
│   │ timestamp       │  │ timestamp       │                                      │
│   │ level           │  │ level           │                                      │
│   │ component       │  │ trigger_reason  │                                      │
│   │ message         │  │ action_taken    │                                      │
│   │ details (JSONB) │  │ resolved        │                                      │
│   └─────────────────┘  └─────────────────┘                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Coleta de Dados

### Fase 1: Backfill Histórico (Manual)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BACKFILL HISTÓRICO                                       │
│                       Executar UMA VEZ localmente                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Terminal Local                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  $ python -m src.data.backfill --days 180 --type all                    │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         src/data/backfill.py                             │   │
│   │                                                                          │   │
│   │   1. Parse argumentos (--days, --type)                                   │   │
│   │   2. Calcular período: hoje - N dias                                     │   │
│   │   3. Para cada tipo de dado:                                             │   │
│   │      ┌──────────────────────────────────────────────────────────────┐   │   │
│   │      │  yfinance.download(ticker, start, end)                        │   │   │
│   │      │                                                               │   │   │
│   │      │  Tickers:                                                     │   │   │
│   │      │  • Iron Ore: GC=F (placeholder - futuro SGX)                  │   │   │
│   │      │  • VALE3: VALE3.SA                                            │   │   │
│   │      │  • USD/BRL: BRL=X                                             │   │   │
│   │      │  • VIX: ^VIX                                                  │   │   │
│   │      │  • IBOV: ^BVSP                                                │   │   │
│   │      └──────────────────────────────────────────────────────────────┘   │   │
│   │   4. Para cada registro no DataFrame:                                    │   │
│   │      ┌──────────────────────────────────────────────────────────────┐   │   │
│   │      │  save_*_price(timestamp, price, volume, ohlc)                 │   │   │
│   │      │  → UPSERT no Supabase                                         │   │   │
│   │      └──────────────────────────────────────────────────────────────┘   │   │
│   │   5. Log resultado                                                       │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                            Supabase                                      │   │
│   │                                                                          │   │
│   │   prices_iron_ore: ~180 registros (1/dia)                               │   │
│   │   prices_vale3: ~180 registros (1/dia)                                  │   │
│   │   auxiliary_data: ~180 registros (1/dia)                                │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fase 2: Coleta Diária Automática (GitHub Actions)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COLETA DIÁRIA AUTOMÁTICA                                 │
│                    .github/workflows/daily-tasks.yml                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Schedule: 0 6 * * 1-5 (06:00 UTC = 03:00 BRT, seg-sex)                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  GitHub Actions Runner (ubuntu-latest)                                   │   │
│   │                                                                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Step 1: actions/checkout@v4                                      │  │   │
│   │  │  → Clona o repositório                                            │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Step 2: actions/setup-python@v5                                  │  │   │
│   │  │  → Python 3.11 + cache pip                                        │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Step 3: pip install -r requirements.txt                         │  │   │
│   │  │  → Instala dependências (yfinance, supabase, pandas, etc.)       │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Step 4: python -m src.data.backfill --days 1                    │  │   │
│   │  │                                                                   │  │   │
│   │  │  Environment Variables (from GitHub Secrets):                    │  │   │
│   │  │  • SUPABASE_URL=${{ secrets.SUPABASE_URL }}                      │  │   │
│   │  │  • SUPABASE_SERVICE_KEY=${{ secrets.SUPABASE_SERVICE_KEY }}      │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Resultado:                                                       │  │   │
│   │  │  • 1 registro em prices_iron_ore                                  │  │   │
│   │  │  • 1 registro em prices_vale3                                     │  │   │
│   │  │  • 1 registro em auxiliary_data                                   │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Custo: ~3 min/execução × 22 dias/mês = ~66 min/mês (FREE TIER: 2000 min)     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Fase 3: Coleta Real-Time (Janela Crítica)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COLETA REAL-TIME (FASE 2)                                │
│                  .github/workflows/collect-realtime.yml                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Schedule: */15 11-14 * * 1-5 (a cada 15 min, 11:00-14:00 UTC = 08:00-11:00 BRT)│
│                                                                                  │
│   Por que esta janela?                                                           │
│   • SGX fecha às 12:00 UTC (09:00 BRT)                                          │
│   • B3 abre às 13:00 UTC (10:00 BRT)                                            │
│   • Janela crítica: 1h para processar sinal antes da abertura B3                │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Job: collect                                                            │   │
│   │                                                                          │   │
│   │  python jobs/scripts/collect_all.py --mode realtime                     │   │
│   │                                                                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  IronOreFetcher.fetch_realtime()                                  │  │   │
│   │  │  • RICs: SZZF5, SZZG5, SZZH5... (12 meses forward)               │  │   │
│   │  │  • Campos: SETTLE, TRDPRC_1, BID, ASK, EXPIR_DATE                │  │   │
│   │  │  • API: LSEG Workspace (real-time)                               │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  Vale3Fetcher.fetch_realtime()                                    │  │   │
│   │  │  • RIC: VALE3.SA                                                  │  │   │
│   │  │  • Campos: TRDPRC_1, BID, ASK, ACVOL_1                           │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                  │                                       │   │
│   │                                  ▼                                       │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  AuxiliaryFetcher.fetch_realtime()                                │  │   │
│   │  │  • RICs: BRL= (USD/BRL), .VIX (VIX)                              │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                         │
│                                        ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  Job: check-signals (depende de collect)                                 │   │
│   │                                                                          │   │
│   │  python -m src.strategy.signal_generator                                │   │
│   │                                                                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │  SignalGenerator.process_and_save_signal()                        │  │   │
│   │  │                                                                   │  │   │
│   │  │  1. get_recent_iron_ore_prices(30 dias)                          │  │   │
│   │  │  2. get_recent_vale3_prices(30 dias)                             │  │   │
│   │  │  3. get_latest_auxiliary_data()                                  │  │   │
│   │  │  4. check_no_trade_conditions() → VIX > 25? Feriado?             │  │   │
│   │  │  5. calculate_iron_ore_return() → retorno, std, zscore           │  │   │
│   │  │  6. calculate_correlation() → correlação rolling 20d             │  │   │
│   │  │  7. check_direction_consistency(2h)                              │  │   │
│   │  │  8. Gerar sinal: LONG | SHORT | None                             │  │   │
│   │  │  9. save_signal() → tabela signals                               │  │   │
│   │  │  10. Notificar Telegram                                          │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Custo: 12 runs/dia × 3 min × 22 dias = ~792 min/mês                          │
│   Total com daily: ~858 min/mês (FREE TIER: 2000 min)                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Modelo de Dados Detalhado

### prices_iron_ore

Armazena preços de futuros de minério de ferro (SGX/DCE).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | Chave primária |
| `timestamp` | TIMESTAMPTZ | Momento do preço (UTC) |
| `source` | VARCHAR(50) | Fonte: 'yahoo', 'lseg', 'sgx', 'dce' |
| `symbol` | VARCHAR(50) | Símbolo: 'SGX_FE_62', 'SZZF5', etc. |
| `price` | DECIMAL(10,2) | Preço de referência |
| `volume` | BIGINT | Volume negociado |
| `open` | DECIMAL(10,2) | Preço de abertura |
| `high` | DECIMAL(10,2) | Máxima |
| `low` | DECIMAL(10,2) | Mínima |
| `close` | DECIMAL(10,2) | Fechamento |
| `created_at` | TIMESTAMPTZ | Data de inserção |

**Índices:**
- `idx_iron_ore_timestamp` - Consultas por período
- `idx_iron_ore_source` - Filtro por fonte

**Constraint:** `UNIQUE(timestamp, source, symbol)`

### prices_vale3

Armazena preços OHLCV de VALE3 na B3.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | Chave primária |
| `timestamp` | TIMESTAMPTZ | Momento do preço (UTC) |
| `source` | VARCHAR(50) | Fonte: 'mt5', 'lseg', 'yahoo' |
| `symbol` | VARCHAR(20) | Sempre 'VALE3' |
| `open` | DECIMAL(10,2) | Preço de abertura |
| `high` | DECIMAL(10,2) | Máxima |
| `low` | DECIMAL(10,2) | Mínima |
| `close` | DECIMAL(10,2) | Fechamento |
| `volume` | BIGINT | Volume financeiro |
| `tick_volume` | BIGINT | Volume de ticks (MT5) |
| `spread` | INTEGER | Spread bid-ask (MT5) |
| `created_at` | TIMESTAMPTZ | Data de inserção |

**Índice:** `idx_vale3_timestamp`

**Constraint:** `UNIQUE(timestamp, source, symbol)`

### auxiliary_data

Dados auxiliares consolidados por timestamp.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | Chave primária |
| `timestamp` | TIMESTAMPTZ | Momento dos dados (UTC) |
| `usd_brl` | DECIMAL(10,4) | Taxa de câmbio USD/BRL |
| `vix` | DECIMAL(10,2) | Índice VIX (volatilidade S&P500) |
| `ibov` | DECIMAL(12,2) | Índice Bovespa |
| `created_at` | TIMESTAMPTZ | Data de inserção |

**Índice:** `idx_auxiliary_timestamp`

**Constraint:** `UNIQUE(timestamp)`

### signals

Sinais de trading gerados pelo sistema.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | BIGSERIAL | Chave primária |
| `timestamp` | TIMESTAMPTZ | Momento da geração |
| `signal_type` | VARCHAR(20) | 'LONG', 'SHORT', 'NEUTRAL', 'EXIT' |
| `symbol` | VARCHAR(20) | Sempre 'VALE3' |
| `confidence` | DECIMAL(5,4) | Confiança (0.0000 a 1.0000) |
| `iron_ore_return` | DECIMAL(10,6) | Retorno do minério |
| `iron_ore_zscore` | DECIMAL(10,4) | Z-score do retorno |
| `features_json` | JSONB | Features usadas na decisão |
| `strategy` | VARCHAR(50) | 'rule_based', 'ml_xgboost' |
| `executed` | BOOLEAN | Se foi executado |
| `created_at` | TIMESTAMPTZ | Data de inserção |

**Índices:**
- `idx_signals_timestamp`
- `idx_signals_executed`

---

## Estratégia de Upsert

O sistema usa **upsert** (insert or update on conflict) para garantir idempotência:

```python
# src/db/client.py
def save_iron_ore_price(...):
    data = {
        "timestamp": timestamp.isoformat(),
        "source": source,
        "symbol": symbol,
        "price": price,
        ...
    }

    # UPSERT: Se (timestamp, source, symbol) já existe, atualiza
    # Se não existe, insere novo registro
    result = client.table("prices_iron_ore").upsert(data).execute()
```

**Benefícios:**
1. **Idempotência**: Rodar backfill múltiplas vezes não duplica dados
2. **Correção**: Dados corrigidos sobrescrevem antigos
3. **Simplicidade**: Não precisa verificar existência antes de inserir

---

## Configuração de Ambiente

### Variáveis Obrigatórias

```bash
# .env

# Supabase (obrigatório)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6...

# LSEG (para coleta real-time)
LSEG_APP_KEY=sua_app_key
LSEG_USERNAME=usuario@empresa.com
LSEG_PASSWORD=senha

# Telegram (opcional, para alertas)
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=987654321
```

### GitHub Secrets

| Secret | Uso | Obrigatório |
|--------|-----|-------------|
| `SUPABASE_URL` | URL do projeto | ✓ |
| `SUPABASE_SERVICE_KEY` | Chave de serviço | ✓ |
| `LSEG_APP_KEY` | API LSEG | Fase 2 |
| `LSEG_USERNAME` | Usuário LSEG | Fase 2 |
| `LSEG_PASSWORD` | Senha LSEG | Fase 2 |
| `TELEGRAM_BOT_TOKEN` | Bot Telegram | Opcional |
| `TELEGRAM_CHAT_ID` | Chat ID | Opcional |

---

## Horários de Mercado e Coleta

```
Timezone: UTC (horários em BRT entre parênteses)

╔═══════════════════════════════════════════════════════════════════════════════╗
║  00:00 ─────────────────────────────────────────────────────────── 24:00 UTC  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  DCE (Dalian, China)                                                          ║
║  ├── 01:00-07:00 UTC (22:00-04:00 BRT D-1)                                   ║
║  └── Futuros de minério de ferro (IO)                                        ║
║                                                                               ║
║  SGX (Singapura)                                                              ║
║  ├── T-Session: 23:25(D-1)-12:00 UTC (20:25-09:00 BRT)                       ║
║  ├── T+1 Session: 12:00-20:45 UTC (09:00-17:45 BRT)                          ║
║  └── Futuros de minério TSI (SZZF, SZZG, ...)                                ║
║                                                                               ║
║  B3 (Brasil)                                                                  ║
║  ├── 13:00-20:55 UTC (10:00-17:55 BRT)                                       ║
║  └── VALE3 (ações)                                                           ║
║                                                                               ║
║  ═══════════════════════════════════════════════════════════════════════════ ║
║                                                                               ║
║  JANELA CRÍTICA: 12:00-13:00 UTC (09:00-10:00 BRT)                           ║
║  ├── SGX fecha (settlement do dia)                                           ║
║  ├── 1 hora para processar sinal                                             ║
║  └── B3 abre (executar ordem)                                                ║
║                                                                               ║
║  COLETAS:                                                                     ║
║  ├── 06:00 UTC (03:00 BRT): Backfill diário (Yahoo Finance)                 ║
║  ├── 11:00-14:00 UTC (08:00-11:00 BRT): Real-time cada 15 min (LSEG)        ║
║  └── 22:00 UTC (19:00 BRT): Relatório diário                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Diagrama de Sequência: Coleta Diária

```
┌─────────┐     ┌─────────────┐     ┌──────────┐     ┌─────────────┐     ┌─────────┐
│ GitHub  │     │   Runner    │     │ backfill │     │  Supabase   │     │  Yahoo  │
│ Actions │     │  (ubuntu)   │     │   .py    │     │  Client     │     │ Finance │
└────┬────┘     └──────┬──────┘     └────┬─────┘     └──────┬──────┘     └────┬────┘
     │                 │                 │                  │                 │
     │  06:00 UTC      │                 │                  │                 │
     │  (cron trigger) │                 │                  │                 │
     │────────────────>│                 │                  │                 │
     │                 │                 │                  │                 │
     │                 │ checkout repo   │                  │                 │
     │                 │─────────────────│                  │                 │
     │                 │                 │                  │                 │
     │                 │ setup python    │                  │                 │
     │                 │─────────────────│                  │                 │
     │                 │                 │                  │                 │
     │                 │ pip install     │                  │                 │
     │                 │─────────────────│                  │                 │
     │                 │                 │                  │                 │
     │                 │ run backfill    │                  │                 │
     │                 │────────────────>│                  │                 │
     │                 │                 │                  │                 │
     │                 │                 │  yf.download()   │                 │
     │                 │                 │─────────────────────────────────────>
     │                 │                 │                  │                 │
     │                 │                 │<─────────────────────────────────────
     │                 │                 │  DataFrame       │                 │
     │                 │                 │                  │                 │
     │                 │                 │  Loop: for each row                │
     │                 │                 │  ┌─────────────────────────────┐   │
     │                 │                 │  │ save_iron_ore_price()       │   │
     │                 │                 │  │────────────────>│           │   │
     │                 │                 │  │                 │ UPSERT    │   │
     │                 │                 │  │<────────────────│ OK        │   │
     │                 │                 │  │                 │           │   │
     │                 │                 │  │ save_vale_price()           │   │
     │                 │                 │  │────────────────>│           │   │
     │                 │                 │  │<────────────────│ OK        │   │
     │                 │                 │  │                 │           │   │
     │                 │                 │  │ save_auxiliary_data()       │   │
     │                 │                 │  │────────────────>│           │   │
     │                 │                 │  │<────────────────│ OK        │   │
     │                 │                 │  └─────────────────────────────┘   │
     │                 │                 │                  │                 │
     │                 │<────────────────│                  │                 │
     │                 │  exit 0         │                  │                 │
     │                 │                 │                  │                 │
     │<────────────────│                 │                  │                 │
     │  success        │                 │                  │                 │
     │                 │                 │                  │                 │
```

---

## Verificação de Dados

### Queries úteis para verificar coleta

```sql
-- Contagem de registros por tabela
SELECT 'prices_iron_ore' as tabela, COUNT(*) as registros FROM prices_iron_ore
UNION ALL
SELECT 'prices_vale3', COUNT(*) FROM prices_vale3
UNION ALL
SELECT 'auxiliary_data', COUNT(*) FROM auxiliary_data
UNION ALL
SELECT 'signals', COUNT(*) FROM signals;

-- Último registro de cada tabela
SELECT 'Iron Ore' as tipo, MAX(timestamp) as ultimo FROM prices_iron_ore
UNION ALL
SELECT 'VALE3', MAX(timestamp) FROM prices_vale3
UNION ALL
SELECT 'Auxiliary', MAX(timestamp) FROM auxiliary_data;

-- Verificar gaps nos dados (dias sem registro)
WITH date_series AS (
  SELECT generate_series(
    (SELECT MIN(timestamp)::date FROM prices_iron_ore),
    CURRENT_DATE,
    '1 day'::interval
  )::date as dia
)
SELECT dia
FROM date_series ds
WHERE NOT EXISTS (
  SELECT 1 FROM prices_iron_ore p
  WHERE p.timestamp::date = ds.dia
)
AND EXTRACT(DOW FROM dia) NOT IN (0, 6)  -- Exclui fins de semana
ORDER BY dia;

-- Estatísticas dos últimos 30 dias
SELECT
  source,
  COUNT(*) as registros,
  MIN(price) as min_price,
  MAX(price) as max_price,
  AVG(price) as avg_price
FROM prices_iron_ore
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY source;
```

---

## Tratamento de Erros

### Estratégia de Retry

```python
# src/data/backfill.py
def backfill_iron_ore(days: int = 30) -> int:
    for name, ticker in symbols.items():
        try:
            data = yf.download(ticker, ...)

            if data.empty:
                logger.warning(f"Nenhum dado para {ticker}")
                continue

            for timestamp, row in data.iterrows():
                result = save_iron_ore_price(...)
                if result:
                    records_inserted += 1

        except Exception as e:
            logger.error(f"Erro ao buscar {name}: {e}")
            # Continua para próximo símbolo
            continue
```

### Logs de Auditoria

Todos os eventos são logados na tabela `system_logs`:

```python
client.table("system_logs").insert({
    "level": "ERROR",
    "component": "backfill",
    "message": "Falha ao buscar dados do Yahoo Finance",
    "details": {
        "ticker": "VALE3.SA",
        "error": str(e),
        "days_requested": 30
    }
}).execute()
```

---

## Resumo dos Arquivos

| Arquivo | Função | Chamado por |
|---------|--------|-------------|
| `src/data/backfill.py` | Backfill histórico | CLI, GitHub Actions |
| `src/db/client.py` | Operações Supabase | Todos os módulos |
| `src/config.py` | Configuração central | Todos os módulos |
| `jobs/ingestion/fetch_iron_ore.py` | Coleta LSEG iron ore | collect_all.py |
| `jobs/ingestion/fetch_vale3.py` | Coleta LSEG VALE3 | collect_all.py |
| `jobs/ingestion/fetch_auxiliary.py` | Coleta LSEG aux | collect_all.py |
| `jobs/scripts/collect_all.py` | Orquestrador coleta | GitHub Actions |
| `.github/workflows/daily-tasks.yml` | Automação diária | GitHub cron |
| `.github/workflows/collect-realtime.yml` | Coleta real-time | GitHub cron |
| `sql/001_initial_schema.sql` | Schema do banco | Supabase SQL Editor |

---

*Documento atualizado em: Janeiro 2026*
