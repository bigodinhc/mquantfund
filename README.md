# QuantFund — Sistema de Trading Quantitativo VALE3/Minério

Sistema de trading quantitativo explorando a relação temporal (lead-lag) entre futuros de minério de ferro (mercado asiático) e ações da VALE3 (B3).

---

## Aviso Importante

> **A hipótese central deste projeto NÃO está validada.** A relação lead-lag entre minério de ferro e VALE3 é uma hipótese a ser testada, não um fato estabelecido. O projeto inclui um gate GO/NO-GO na Semana 2 para validação estatística antes de qualquer capital ser colocado em risco.

---

## Visão Geral

### Hipótese

Variações significativas nos preços de futuros de minério de ferro na sessão asiática (SGX/DCE) contêm informação preditiva para retornos de VALE3 no pregão brasileiro seguinte.

### Mecanismo Proposto

- Vale deriva ~80% da receita de Iron Solutions
- ~60% dos contratos Vale precificados via índices linked ao SGX
- Gap temporal de ~1h entre fechamento SGX (09:00 BRT) e abertura B3 (10:00 BRT)

### Timeline

```
SEMANA 1: Infraestrutura + Dados
SEMANA 2: Validação Estatística → GATE GO/NO-GO
SEMANA 3: Execução + Risco (se GO)
SEMANA 4: Paper Trading + Go-Live 10%
```

---

## Stack Tecnológica

| Componente | Tecnologia | Custo |
|------------|------------|-------|
| **Database** | Supabase (PostgreSQL gerenciado) | Grátis |
| **Backend/Bot** | Railway (Python 24/7) | ~R$25-50/mês |
| **Repositório** | GitHub | Grátis |
| **Corretora** | Clear (MT5) | Grátis |
| **MT5 Runtime** | PC local (Windows) | Grátis |
| **Alertas** | Telegram Bot | Grátis |
| **Dashboard** | Streamlit (Railway) | Incluído |

**Custo mensal total**: ~R$25-50/mês

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA DO SISTEMA                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │   RAILWAY    │     │   SUPABASE   │     │   GITHUB     │   │
│   │              │     │              │     │              │   │
│   │ • Scheduler  │────▶│ • PostgreSQL │     │ • Código     │   │
│   │ • Bot 24/7   │     │ • Dados      │     │ • CI/CD      │   │
│   │ • Dashboard  │     │ • Real-time  │     │              │   │
│   └──────────────┘     └──────────────┘     └──────────────┘   │
│          │                    ▲                                  │
│          │                    │                                  │
│          ▼                    │                                  │
│   ┌──────────────┐           │                                  │
│   │  SEU PC      │───────────┘                                  │
│   │              │                                              │
│   │ • MT5 Clear  │  ◀── Necessário para execução de ordens     │
│   │ • Ordens     │                                              │
│   └──────────────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estrutura do Projeto

```
quantfund/
├── README.md                 # Este arquivo
├── CLAUDE.md                 # Contexto para Claude AI
├── TRACK.md                  # Tracking de tarefas por semana
├── roadmap-fundo-quant-vale3-4semanas.md  # Roadmap consolidado
│
├── src/
│   ├── __init__.py
│   ├── main_loop.py          # Loop principal de execução
│   │
│   ├── data/                 # Conectores e coleta de dados
│   │   ├── __init__.py
│   │   ├── iron_ore_fetcher.py   # Yahoo Finance / Investing.com
│   │   ├── vale_fetcher.py       # MT5 Clear
│   │   ├── auxiliary_fetcher.py  # USD/BRL, VIX
│   │   └── backfill.py           # Carga histórica
│   │
│   ├── db/                   # Conexão Supabase
│   │   ├── __init__.py
│   │   ├── client.py             # Cliente Supabase
│   │   └── models.py             # Modelos de dados
│   │
│   ├── features/             # Feature engineering
│   │   ├── __init__.py
│   │   ├── returns.py
│   │   ├── volatility.py
│   │   ├── zscore.py
│   │   └── alignment.py
│   │
│   ├── strategy/             # Geração de sinais
│   │   ├── __init__.py
│   │   └── signal_generator.py
│   │
│   ├── backtest/             # Motor de backtest
│   │   ├── __init__.py
│   │   └── engine.py
│   │
│   ├── execution/            # Execução de ordens
│   │   ├── __init__.py
│   │   └── mt5_connector.py
│   │
│   ├── risk/                 # Gestão de risco
│   │   ├── __init__.py
│   │   ├── position_sizing.py
│   │   ├── loss_limits.py
│   │   ├── stop_manager.py
│   │   └── kill_switch.py
│   │
│   ├── alerts/               # Alertas e comandos
│   │   ├── __init__.py
│   │   └── telegram_bot.py
│   │
│   ├── scheduler/            # Jobs agendados
│   │   ├── __init__.py
│   │   └── jobs.py
│   │
│   ├── utils/                # Utilitários
│   │   ├── __init__.py
│   │   └── retry.py
│   │
│   └── dashboard/            # Interface web
│       ├── __init__.py
│       └── app.py
│
├── notebooks/                # Análises e validação
│   ├── 01_exploratory.ipynb
│   ├── 02_correlation_lags.ipynb
│   ├── 03_granger_causality.ipynb
│   ├── 04_cointegration.ipynb
│   ├── 05_subperiod_stability.ipynb
│   ├── 06_backtest_walkforward.ipynb
│   └── 07_sensitivity.ipynb
│
├── sql/                      # Scripts SQL para Supabase
│   └── 001_initial_schema.sql
│
├── docs/                     # Documentação
│   ├── decision_gate_week2.md
│   ├── operations_manual.md
│   ├── troubleshooting.md
│   └── daily_checklist.md
│
├── tests/                    # Testes
│   ├── __init__.py
│   ├── test_data/
│   ├── test_features/
│   ├── test_strategy/
│   └── test_risk/
│
├── .env.example              # Template de variáveis de ambiente
├── .gitignore
├── pyproject.toml            # Dependências (Poetry)
├── requirements.txt          # Alternativa pip
└── Procfile                  # Config Railway
```

---

## Instalação

### Pré-requisitos

- Python 3.11+
- Conta Supabase (grátis)
- Conta Railway (grátis para iniciar)
- Conta Clear com acesso MT5
- Conta Telegram (para alertas)
- PC Windows (para MT5)

### Setup Local

```bash
# 1. Clonar repositório
git clone https://github.com/bigodinhc/mquantfund.git
cd mquantfund

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instalar dependências
pip install -r requirements.txt
# ou com Poetry:
poetry install

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# 5. Verificar instalação
python -m pytest tests/
```

### Setup Supabase

1. Criar projeto em [supabase.com](https://supabase.com)
2. Ir em Settings → API e copiar:
   - Project URL
   - anon/public key
   - service_role key (para backend)
3. Ir em SQL Editor e executar `sql/001_initial_schema.sql`

### Setup Railway

1. Criar projeto em [railway.app](https://railway.app)
2. Conectar ao repositório GitHub
3. Configurar variáveis de ambiente (mesmo do .env)
4. Deploy automático a cada push

### Setup Clear MT5

1. Solicitar acesso MT5 no app/site da Clear
2. Instalar MetaTrader 5 no PC
3. Login com credenciais recebidas
4. Testar conexão: `python -c "import MetaTrader5; print(MetaTrader5.initialize())"`

---

## Configuração

### Variáveis de Ambiente (.env)

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# MetaTrader 5
MT5_LOGIN=12345678
MT5_PASSWORD=sua_senha
MT5_SERVER=Clear-Real  # ou Clear-Demo

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321

# Trading
CAPITAL=50000                 # Capital total em R$
RISK_PER_TRADE=0.02          # 2% de risco por trade
MAX_POSITION_PCT=0.20        # Máximo 20% da conta
DAILY_LOSS_LIMIT=0.025       # 2.5% perda diária máxima
```

---

## Uso

### Coleta de Dados (Local)

```bash
# Executar backfill histórico (6-12 meses)
python -m src.data.backfill

# Iniciar coleta contínua
python -m src.scheduler.jobs
```

### Análise e Validação

```bash
# Executar notebooks de validação
jupyter notebook notebooks/
```

### Trading

```bash
# Modo paper trading (demo)
python -m src.main_loop --mode paper

# Modo real (após paper trading bem sucedido)
python -m src.main_loop --mode live
```

### Dashboard

```bash
# Iniciar dashboard local
streamlit run src/dashboard/app.py

# Ou acessar via Railway (após deploy)
# https://seu-projeto.up.railway.app
```

### Comandos Telegram

| Comando | Descrição |
|---------|-----------|
| `/status` | Status atual do sistema |
| `/positions` | Posições abertas |
| `/pnl` | P&L do dia |
| `/pause` | Pausar trading |
| `/resume` | Retomar trading |
| `/kill` | EMERGÊNCIA: fechar tudo |

---

## Gestão de Risco

### Limites de Perda

| Período | Limite | Ação |
|---------|--------|------|
| Diário | 2.5% | HALT automático |
| Semanal | 5% | Reduzir sizing 50% |
| Mensal | 10% | Cessar trading 5 dias |
| Drawdown máximo | 20% | FULL STOP |

### Kill Switches

1. **Nível 1 (Automático)**: Loss limit, dados stale, ordens rejeitadas
2. **Nível 2 (Confirmação)**: Divergência de preços, perdedores consecutivos
3. **Nível 3 (Manual)**: Posição > 10%, override de limites
4. **Nível 4 (Pânico)**: Comando `/kill` no Telegram

---

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [TRACK.md](TRACK.md) | Tracking de tarefas por semana |
| [CLAUDE.md](CLAUDE.md) | Contexto para Claude AI |
| [Roadmap](roadmap-fundo-quant-vale3-4semanas.md) | Plano completo do projeto |

---

## Critérios GO/NO-GO (Semana 2)

### GO (todos devem ser atendidos)

- [ ] Granger significativo (p < 0.05) em 2+ lags
- [ ] Correlação defasada > 0.3 em múltiplos subperíodos
- [ ] Sharpe walk-forward > 1.0 após custos (0.25%)
- [ ] Win rate > 50%
- [ ] Max drawdown histórico < 15%

### NO-GO (qualquer um cancela)

- [ ] Nenhuma significância estatística
- [ ] Sharpe < 0.5 após custos
- [ ] Inversão de sinal entre subperíodos

---

## Escalamento de Capital

| Semana | Capital | Condição |
|--------|---------|----------|
| 4 | 10% (R$2-5k) | Go-live inicial |
| 6 | 25% (R$5-12.5k) | 2 semanas sem erros |
| 8 | 50% (R$10-25k) | Performance OK |
| 10+ | 100% (R$20-50k) | Confiança estabelecida |

---

## Custos

### Infraestrutura (Mensal)

| Serviço | Custo |
|---------|-------|
| Supabase | Grátis (Free tier: 500MB, 2GB transfer) |
| Railway | ~R$25-50/mês ($5-10 USD) |
| Clear | Grátis (corretagem zero) |
| Telegram | Grátis |
| **Total** | **~R$25-50/mês** |

### Trading

| Item | Custo |
|------|-------|
| Emolumentos B3 | ~0.03% por lado |
| Corretagem Clear | Zero |
| Spread VALE3 | ~0.03-0.05% |
| **Total round-trip** | **~0.15-0.25%** |

---

## Troubleshooting

### MT5 não conecta
```bash
# Verificar se MT5 está rodando
# Verificar credenciais no .env
# Testar manualmente:
python -c "import MetaTrader5 as mt5; print(mt5.initialize())"
```

### Supabase erro de conexão
```bash
# Verificar URL e keys no .env
# Testar conexão:
python -c "from supabase import create_client; print('OK')"
```

### Railway não deploya
```bash
# Verificar Procfile existe
# Verificar requirements.txt válido
# Ver logs no dashboard Railway
```

---

## Contribuição

Este é um projeto pessoal para fins educacionais. Não aceita contribuições externas no momento.

---

## Disclaimer

**AVISO DE RISCO**: Trading envolve risco significativo de perda. Este sistema é experimental e não há garantia de lucros. Nunca invista mais do que você pode perder. O desenvolvedor não se responsabiliza por perdas financeiras decorrentes do uso deste software.

---

## Licença

Privado - Uso pessoal apenas.

---

## Contato

Para questões sobre o projeto, abra uma issue no repositório.
