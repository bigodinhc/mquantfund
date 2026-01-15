# ROADMAP MVP: Sistema de Trading Minério × VALE3

## Documento de Implementação Técnica

**Versão**: 1.0  
**Escopo**: MVP operacional em 4 semanas  
**Capital alvo**: R$20-50k  

---

## 1. DEFINIÇÃO DO MVP

### 1.1 O que É o MVP

O MVP (Minimum Viable Product) é a versão mais simples do sistema que permite:

1. **Coletar dados** de minério de ferro (SGX) e VALE3 automaticamente
2. **Validar estatisticamente** a hipótese lead-lag
3. **Gerar sinais** baseados em regras simples
4. **Executar ordens** automaticamente na B3
5. **Monitorar** performance e riscos em tempo real
6. **Pausar** automaticamente em condições adversas

### 1.2 O que NÃO É o MVP

- ❌ Machine Learning sofisticado (fase 2)
- ❌ Análise de sentimento/NLP (fase 3)
- ❌ Multi-ativos ou multi-estratégia
- ❌ Infraestrutura de alta disponibilidade
- ❌ Interface gráfica elaborada
- ❌ Backtesting engine próprio completo

### 1.3 Critérios de Sucesso do MVP

| Critério | Métrica | Threshold |
|----------|---------|-----------|
| Funcional | Sistema operando sem intervenção | 5 dias consecutivos |
| Dados | Coleta sem gaps >5min | 99% uptime |
| Execução | Ordens executadas corretamente | 100% accuracy |
| Latência | Sinal → Ordem | <30 segundos |
| Risco | Kill switches funcionando | 100% dos triggers |

---

## 2. STACK TECNOLÓGICO - DECISÕES FINAIS

### 2.1 Visão Geral da Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        STACK MVP                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LINGUAGEM         Python 3.11+                                 │
│  ──────────────────────────────────────────────────────────────│
│  DADOS MINÉRIO     Yahoo Finance API + Investing.com scraping   │
│  DADOS VALE3       MetaTrader 5 (via corretora)                 │
│  ──────────────────────────────────────────────────────────────│
│  DATABASE          PostgreSQL 15 + TimescaleDB extension        │
│  CACHE             Redis (opcional MVP)                         │
│  ──────────────────────────────────────────────────────────────│
│  EXECUÇÃO          MetaTrader 5 Python API                      │
│  CORRETORA         Clear ou XP (zero corretagem)                │
│  ──────────────────────────────────────────────────────────────│
│  SCHEDULING        APScheduler + Cron                           │
│  ALERTAS           Telegram Bot API                             │
│  ──────────────────────────────────────────────────────────────│
│  MONITORING        Grafana + InfluxDB (ou simples: logs + CSV)  │
│  ──────────────────────────────────────────────────────────────│
│  INFRA             VPS Linux (Contabo/DigitalOcean)             │
│                    OU máquina local (fase inicial)              │
│  ──────────────────────────────────────────────────────────────│
│  VERSIONAMENTO     Git + GitHub (repo privado)                  │
│  ──────────────────────────────────────────────────────────────│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Justificativa das Escolhas

#### Por que Python?

| Fator | Avaliação |
|-------|-----------|
| Ecossistema quant | Pandas, NumPy, Statsmodels, scikit-learn |
| Integração MT5 | Biblioteca oficial MetaTrader5 |
| Tempo de desenvolvimento | Mais rápido que Java/C++ |
| Performance | Suficiente para latência de segundos |
| Sua familiaridade | Já usa Python profissionalmente |

**Alternativas descartadas**:
- R: Pior integração com execução
- Java: Overhead de desenvolvimento para MVP
- C++: Desnecessário para esta latência

#### Por que MetaTrader 5?

| Fator | MT5 | Alternativas |
|-------|-----|--------------|
| Custo | Grátis via corretora | Cedro: R$200-500/mês |
| API Python | Oficial, bem documentada | Varia |
| Corretoras BR | Clear, XP, Rico, Modal | Limitado |
| Dados real-time | Incluído | Custo adicional |
| Execução | Integrada | Precisa integrar |

**Limitações do MT5**: 
- Apenas ativos da corretora (não tem SGX direto)
- Precisa complementar com fonte externa para minério

#### Por que PostgreSQL + TimescaleDB?

| Fator | PostgreSQL | SQLite | MongoDB |
|-------|------------|--------|---------|
| Time-series | TimescaleDB extension | Ruim | Razoável |
| Queries analíticas | Excelente | Limitado | Ruim |
| Confiabilidade | Alta | Média | Alta |
| Complexidade | Média | Baixa | Média |
| Escalabilidade | Alta | Baixa | Alta |

**Para MVP**: SQLite é aceitável nas primeiras 2 semanas. Migrar para PostgreSQL na semana 3.

### 2.3 Stack Completa com Versões

```yaml
# requirements.txt - Core
python: ">=3.11"
MetaTrader5: "5.0.45"
pandas: ">=2.0"
numpy: ">=1.24"
sqlalchemy: ">=2.0"
psycopg2-binary: ">=2.9"  # PostgreSQL
redis: ">=4.5"  # Opcional MVP

# requirements.txt - Data
yfinance: ">=0.2.28"
requests: ">=2.31"
beautifulsoup4: ">=4.12"  # Scraping backup
websocket-client: ">=1.6"

# requirements.txt - Analysis
statsmodels: ">=0.14"
scipy: ">=1.11"
scikit-learn: ">=1.3"  # Fase 2

# requirements.txt - Operations
APScheduler: ">=3.10"
python-telegram-bot: ">=20.0"
loguru: ">=0.7"
python-dotenv: ">=1.0"

# requirements.txt - Testing
pytest: ">=7.4"
pytest-asyncio: ">=0.21"
```

---

## 3. ARQUITETURA DO SISTEMA

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ARQUITETURA MVP                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                     CAMADA DE DADOS                              │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │      │
│    │   │   MINÉRIO    │    │    VALE3     │    │   AUXILIAR   │     │      │
│    │   │              │    │              │    │              │     │      │
│    │   │ • Yahoo Fin  │    │ • MT5 API    │    │ • USD/BRL    │     │      │
│    │   │ • Investing  │    │ • Real-time  │    │ • VIX        │     │      │
│    │   │ • Backup API │    │ • Histórico  │    │ • Calendário │     │      │
│    │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │      │
│    │          │                   │                   │              │      │
│    │          └───────────────────┼───────────────────┘              │      │
│    │                              ▼                                  │      │
│    │                    ┌──────────────────┐                         │      │
│    │                    │    INGESTÃO      │                         │      │
│    │                    │   data_ingestion │                         │      │
│    │                    └────────┬─────────┘                         │      │
│    │                             │                                   │      │
│    └─────────────────────────────┼───────────────────────────────────┘      │
│                                  ▼                                          │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CAMADA DE STORAGE                             │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────────────────────────────────────────────┐      │      │
│    │   │              PostgreSQL + TimescaleDB                │      │      │
│    │   │                                                      │      │      │
│    │   │  • prices_iron_ore (hypertable)                     │      │      │
│    │   │  • prices_vale3 (hypertable)                        │      │      │
│    │   │  • signals (histórico de sinais)                    │      │      │
│    │   │  • orders (histórico de ordens)                     │      │      │
│    │   │  • positions (posições atuais)                      │      │      │
│    │   │  • metrics (métricas diárias)                       │      │      │
│    │   └──────────────────────────────────────────────────────┘      │      │
│    │                             │                                   │      │
│    └─────────────────────────────┼───────────────────────────────────┘      │
│                                  ▼                                          │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CAMADA DE ANÁLISE                             │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │      │
│    │   │   FEATURES   │    │   VALIDAÇÃO  │    │    SINAL     │     │      │
│    │   │              │    │              │    │              │     │      │
│    │   │ • Retornos   │───▶│ • Granger    │───▶│ • Threshold  │     │      │
│    │   │ • Volatility │    │ • Correlação │    │ • Filtros    │     │      │
│    │   │ • Momentum   │    │ • Regime     │    │ • Confiança  │     │      │
│    │   └──────────────┘    └──────────────┘    └──────────────┘     │      │
│    │                                                  │              │      │
│    └──────────────────────────────────────────────────┼──────────────┘      │
│                                                       ▼                     │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CAMADA DE DECISÃO                             │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │      │
│    │   │    RISCO     │    │   POSITION   │    │   DECISÃO    │     │      │
│    │   │              │    │    SIZING    │    │              │     │      │
│    │   │ • Drawdown   │───▶│ • ATR-based  │───▶│ • BUY/SELL   │     │      │
│    │   │ • Exposure   │    │ • Kelly      │    │ • HOLD       │     │      │
│    │   │ • Limits     │    │ • Max pos    │    │ • NO-TRADE   │     │      │
│    │   └──────────────┘    └──────────────┘    └──────────────┘     │      │
│    │                                                  │              │      │
│    └──────────────────────────────────────────────────┼──────────────┘      │
│                                                       ▼                     │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CAMADA DE EXECUÇÃO                            │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │      │
│    │   │  ORDER MGR   │    │   MT5 API    │    │  RECONCILE   │     │      │
│    │   │              │    │              │    │              │     │      │
│    │   │ • Criar      │───▶│ • Submit     │───▶│ • Confirmar  │     │      │
│    │   │ • Modificar  │    │ • Monitor    │    │ • Ajustar    │     │      │
│    │   │ • Cancelar   │    │ • Cancel     │    │ • Registrar  │     │      │
│    │   └──────────────┘    └──────────────┘    └──────────────┘     │      │
│    │                                                  │              │      │
│    └──────────────────────────────────────────────────┼──────────────┘      │
│                                                       ▼                     │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                    CAMADA DE MONITORING                          │      │
│    ├─────────────────────────────────────────────────────────────────┤      │
│    │                                                                  │      │
│    │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │      │
│    │   │    LOGS      │    │   ALERTAS    │    │  DASHBOARD   │     │      │
│    │   │              │    │              │    │              │     │      │
│    │   │ • Loguru     │    │ • Telegram   │    │ • Grafana    │     │      │
│    │   │ • Arquivos   │    │ • Email      │    │ • CSV/Excel  │     │      │
│    │   │ • Database   │    │ • SMS        │    │ • Streamlit  │     │      │
│    │   └──────────────┘    └──────────────┘    └──────────────┘     │      │
│    │                                                                 │      │
│    └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐      │
│    │                      KILL SWITCHES                               │      │
│    │  [Loss Limit] [Data Stale] [API Down] [Manual] [Correlation]    │      │
│    └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Fluxo de Dados Temporal

```
TIMELINE DIÁRIO (Horário de Brasília)

21:00 (D-1)  ──────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ SESSÃO NOTURNA SGX (21:25 - 05:00 BRT)                      │
    │   │                                                              │
    │   │  • Coletar preços minério a cada 5 min                      │
    │   │  • Calcular variação acumulada                              │
    │   │  • Detectar movimentos >1.5σ                                │
    │   └─────────────────────────────────────────────────────────────┘
    │
05:00 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ PRÉ-ABERTURA (05:00 - 09:45)                                │
    │   │                                                              │
    │   │  • Consolidar dados da sessão asiática                      │
    │   │  • Gerar sinal preliminar                                   │
    │   │  • Calcular position size                                   │
    │   │  • Verificar filtros (VIX, USD/BRL, calendário)             │
    │   │  • Preparar ordem (se sinal ativo)                          │
    │   └─────────────────────────────────────────────────────────────┘
    │
09:45 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ LEILÃO DE ABERTURA B3 (09:45 - 10:00)                       │
    │   │                                                              │
    │   │  • NÃO executar durante leilão                              │
    │   │  • Monitorar preço teórico                                  │
    │   └─────────────────────────────────────────────────────────────┘
    │
10:00 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ EXECUÇÃO (10:05 - 10:30)                                    │
    │   │                                                              │
    │   │  • Aguardar 5 min após abertura (evitar volatilidade)       │
    │   │  • Reavaliar sinal com preço de abertura real               │
    │   │  • Executar ordem se condições mantidas                     │
    │   │  • Confirmar fill e registrar                               │
    │   └─────────────────────────────────────────────────────────────┘
    │
10:30 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ GESTÃO INTRADAY (10:30 - 17:30)                             │
    │   │                                                              │
    │   │  • Monitorar posição aberta                                 │
    │   │  • Verificar stops e targets                                │
    │   │  • Atualizar trailing stop se aplicável                     │
    │   │  • Coletar dados VALE3 para histórico                       │
    │   └─────────────────────────────────────────────────────────────┘
    │
17:30 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ FECHAMENTO (17:30 - 18:00)                                  │
    │   │                                                              │
    │   │  • Avaliar se fecha posição (time stop?)                    │
    │   │  • Calcular P&L do dia                                      │
    │   │  • Atualizar métricas                                       │
    │   │  • Gerar relatório diário                                   │
    │   │  • Enviar resumo via Telegram                               │
    │   └─────────────────────────────────────────────────────────────┘
    │
18:00 ───────────────────────────────────────────────────────────────────►
    │
    │   ┌─────────────────────────────────────────────────────────────┐
    │   │ PÓS-MERCADO (18:00 - 21:00)                                 │
    │   │                                                              │
    │   │  • Reconciliação com extrato corretora                      │
    │   │  • Backup de dados                                          │
    │   │  • Análise de performance                                   │
    │   │  • Preparar para próxima sessão asiática                    │
    │   └─────────────────────────────────────────────────────────────┘
    │
21:00 ───────────────────────────────────────────────────────────────────►
    │
    └── REINÍCIO DO CICLO
```

### 3.3 Diagrama de Estados do Sistema

```
                    ┌─────────────┐
                    │   IDLE      │
                    │ (Aguardando)│
                    └──────┬──────┘
                           │
                           │ Sessão asiática inicia
                           ▼
                    ┌─────────────┐
                    │  COLETANDO  │◄──────────────────┐
                    │   DADOS     │                   │
                    └──────┬──────┘                   │
                           │                         │
                           │ Dados suficientes       │ Dados stale
                           ▼                         │ (retry)
                    ┌─────────────┐                  │
                    │  ANALISANDO │──────────────────┘
                    │             │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ NO-TRADE │ │  SIGNAL  │ │  ERROR   │
       │          │ │  ATIVO   │ │          │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            │            │            │
            ▼            ▼            ▼
       ┌─────────────────────────────────────┐
       │              AGUARDANDO             │
       │           ABERTURA B3               │
       └──────────────────┬──────────────────┘
                          │
                          │ 10:05 BRT
                          ▼
                   ┌─────────────┐
                   │  EXECUTANDO │
                   │    ORDEM    │
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
              ▼           ▼           ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │   FILL   │ │ PARTIAL  │ │ REJECTED │
       │ COMPLETO │ │   FILL   │ │          │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │            │            │
            └────────────┼────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  POSIÇÃO    │
                  │   ABERTA    │
                  └──────┬──────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │   STOP   │   │  TARGET  │   │   TIME   │
   │   HIT    │   │   HIT    │   │   STOP   │
   └────┬─────┘   └────┬─────┘   └────┬─────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
                ┌─────────────┐
                │   POSIÇÃO   │
                │  FECHADA    │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │ REGISTRANDO │
                │  & REPORT   │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │    IDLE     │
                └─────────────┘


    ╔═══════════════════════════════════════════════════════════╗
    ║              ESTADOS DE EMERGÊNCIA                        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║   Qualquer estado ──► KILL_SWITCH                        ║
    ║                                                           ║
    ║   Triggers:                                               ║
    ║   • Loss limit diário atingido                           ║
    ║   • API MT5 não responde >60s                            ║
    ║   • Dados stale >15min                                   ║
    ║   • Comando manual                                        ║
    ║   • Drawdown >15%                                        ║
    ║                                                           ║
    ║   Ações:                                                  ║
    ║   • Cancelar ordens pendentes                            ║
    ║   • Fechar posições (opcional - configurável)            ║
    ║   • Alertar via Telegram                                 ║
    ║   • Aguardar intervenção manual                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
```

---

## 4. ESTRUTURA DO PROJETO

### 4.1 Hierarquia de Diretórios

```
iron-vale-trading/
│
├── README.md                      # Documentação principal
├── requirements.txt               # Dependências Python
├── .env.example                   # Template de variáveis de ambiente
├── .gitignore                     # Arquivos ignorados pelo Git
├── setup.py                       # Instalação do pacote
│
├── config/                        # Configurações
│   ├── __init__.py
│   ├── settings.py               # Configurações gerais
│   ├── trading_params.py         # Parâmetros de trading
│   └── credentials.py            # Gerenciamento de credenciais
│
├── src/                           # Código fonte principal
│   ├── __init__.py
│   │
│   ├── data/                      # Camada de dados
│   │   ├── __init__.py
│   │   ├── iron_ore_fetcher.py   # Coleta dados minério
│   │   ├── vale_fetcher.py       # Coleta dados VALE3 via MT5
│   │   ├── auxiliary_fetcher.py  # USD/BRL, VIX, calendário
│   │   └── data_validator.py     # Validação de dados
│   │
│   ├── storage/                   # Camada de storage
│   │   ├── __init__.py
│   │   ├── database.py           # Conexão PostgreSQL
│   │   ├── models.py             # SQLAlchemy models
│   │   └── repositories.py       # Data access layer
│   │
│   ├── analysis/                  # Camada de análise
│   │   ├── __init__.py
│   │   ├── features.py           # Cálculo de features
│   │   ├── validation.py         # Testes estatísticos (Granger, etc)
│   │   └── signal_generator.py   # Geração de sinais
│   │
│   ├── risk/                      # Gestão de risco
│   │   ├── __init__.py
│   │   ├── position_sizing.py    # Cálculo de tamanho
│   │   ├── risk_limits.py        # Limites e checks
│   │   └── kill_switch.py        # Emergency stops
│   │
│   ├── execution/                 # Execução de ordens
│   │   ├── __init__.py
│   │   ├── mt5_connector.py      # Interface com MT5
│   │   ├── order_manager.py      # Gerenciamento de ordens
│   │   └── reconciliation.py     # Reconciliação
│   │
│   ├── monitoring/                # Monitoramento
│   │   ├── __init__.py
│   │   ├── logger.py             # Configuração de logs
│   │   ├── alerts.py             # Sistema de alertas
│   │   ├── metrics.py            # Cálculo de métricas
│   │   └── dashboard.py          # Dashboard (Streamlit)
│   │
│   └── core/                      # Orquestração
│       ├── __init__.py
│       ├── scheduler.py          # Agendamento de tarefas
│       ├── state_machine.py      # Máquina de estados
│       └── main_loop.py          # Loop principal
│
├── scripts/                       # Scripts utilitários
│   ├── setup_database.py         # Criar tabelas
│   ├── backfill_data.py          # Preencher histórico
│   ├── run_validation.py         # Executar validação estatística
│   └── generate_report.py        # Gerar relatórios
│
├── tests/                         # Testes automatizados
│   ├── __init__.py
│   ├── test_data_fetchers.py
│   ├── test_signal_generator.py
│   ├── test_position_sizing.py
│   ├── test_order_manager.py
│   └── test_kill_switch.py
│
├── notebooks/                     # Jupyter notebooks
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_statistical_validation.ipynb
│   ├── 03_backtest_rules.ipynb
│   └── 04_parameter_sensitivity.ipynb
│
├── data/                          # Dados locais
│   ├── raw/                       # Dados brutos
│   ├── processed/                 # Dados processados
│   └── exports/                   # Relatórios exportados
│
├── logs/                          # Arquivos de log
│   ├── trading.log
│   ├── errors.log
│   └── audit.log
│
└── docs/                          # Documentação
    ├── architecture.md
    ├── operations_manual.md
    └── troubleshooting.md
```

### 4.2 Arquivo de Configuração Principal

```python
# config/settings.py - Estrutura

ENVIRONMENT = "dev"  # dev | staging | production

DATA_SOURCES = {
    "iron_ore": {
        "primary": "yahoo_finance",
        "backup": "investing_com",
        "symbol": "TIO=F",  # SGX Iron Ore
        "interval": "5m",
    },
    "vale": {
        "source": "mt5",
        "symbol": "VALE3",
        "timeframe": "M5",
    },
    "auxiliary": {
        "usd_brl": "USDBRL=X",
        "vix": "^VIX",
    }
}

TRADING = {
    "signal": {
        "threshold_std": 1.5,
        "lookback_volatility": 20,
        "min_confidence": 0.6,
    },
    "execution": {
        "wait_after_open_minutes": 5,
        "max_slippage_percent": 0.3,
        "order_type": "LIMIT",
    },
    "position": {
        "max_holding_days": 5,
        "partial_take_profit": 0.5,
    }
}

RISK = {
    "position_sizing": {
        "method": "atr_based",
        "risk_per_trade_percent": 2.0,
        "max_position_percent": 20.0,
    },
    "stops": {
        "initial_stop_atr_mult": 2.0,
        "trailing_stop_atr_mult": 1.5,
        "breakeven_at_risk_mult": 1.0,
    },
    "limits": {
        "daily_loss_percent": 2.5,
        "weekly_loss_percent": 5.0,
        "monthly_loss_percent": 10.0,
        "max_drawdown_percent": 20.0,
    }
}

MONITORING = {
    "alerts": {
        "telegram_enabled": True,
        "email_enabled": False,
        "sms_enabled": False,
    },
    "logging": {
        "level": "INFO",
        "retention_days": 90,
    }
}
```

---

## 5. FERRAMENTAS ESPECÍFICAS

### 5.1 Matriz de Ferramentas por Categoria

| Categoria | Ferramenta | Propósito | Prioridade MVP |
|-----------|------------|-----------|----------------|
| **IDE** | VS Code + Python extension | Desenvolvimento | ESSENCIAL |
| **IDE** | PyCharm Community | Alternativa | OPCIONAL |
| **Versionamento** | Git + GitHub | Controle de código | ESSENCIAL |
| **Database** | DBeaver | GUI para PostgreSQL | RECOMENDADO |
| **Database** | pgAdmin | Alternativa GUI | OPCIONAL |
| **API Testing** | Postman | Testar endpoints | ÚTIL |
| **Notebooks** | Jupyter Lab | Análise exploratória | ESSENCIAL |
| **Monitoring** | Grafana | Dashboards | FASE 2 |
| **Monitoring** | Streamlit | Dashboard simples | MVP OK |
| **Alertas** | Telegram Bot | Notificações | ESSENCIAL |
| **Docs** | Notion ou Obsidian | Documentação | RECOMENDADO |
| **Backup** | rclone | Sync para cloud | RECOMENDADO |

### 5.2 Fontes de Dados - Detalhamento

#### Minério de Ferro (SGX TSI Iron Ore 62% CFR)

| Fonte | Tipo | Delay | Custo | Confiabilidade |
|-------|------|-------|-------|----------------|
| **Yahoo Finance** | API | 15-20 min | Grátis | MÉDIA |
| **Investing.com** | Scraping | Real-time* | Grátis | MÉDIA |
| **TradingView** | Webhook | Near real-time | Grátis** | ALTA |
| **Quandl/Nasdaq** | API | EOD | Grátis/Pago | ALTA |
| **Interactive Brokers** | API | Real-time | Conta | ALTA |

*Sujeito a bloqueio  
**Precisa conta

**Recomendação MVP**: Yahoo Finance como primário + Investing.com scraping como backup.

#### VALE3

| Fonte | Tipo | Delay | Custo |
|-------|------|-------|-------|
| **MT5 via Clear/XP** | API nativa | Real-time | Grátis |
| **TradingView** | Webhook | Real-time | Grátis |
| **B3 Market Data** | Direto | Real-time | Caro |

**Recomendação MVP**: MT5 via corretora (já inclui execução).

### 5.3 Corretoras Compatíveis

| Corretora | MT5 | API própria | Corretagem VALE3 | Recomendação |
|-----------|-----|-------------|------------------|--------------|
| **Clear** | ✅ | Via MT5 | R$0 | ⭐ PRIMEIRA OPÇÃO |
| **XP** | ✅ | Cedro | R$0-4,90 | ⭐ BOA OPÇÃO |
| **Rico** | ✅ | Via MT5 | R$0 | OK |
| **Modal** | ✅ | Limitada | R$0 | OK |
| **BTG** | ❌ | REST | Variável | Não para MVP |

---

## 6. O QUE NÃO USAR (E POR QUÊ)

### 6.1 Tecnologias a Evitar no MVP

| Tecnologia | Por que evitar | Quando considerar |
|------------|----------------|-------------------|
| **Kubernetes** | Overhead operacional enorme | >R$500k capital |
| **Kafka** | Complexidade desnecessária | Multi-estratégia |
| **MongoDB** | Ruim para time-series | Nunca para este caso |
| **Node.js** | Ecossistema quant fraco | Frontend separado |
| **Terraform** | Prematura para MVP | Infra multi-cloud |
| **ML complexo (Deep Learning)** | Overfitting garantido | Após 1 ano de dados |
| **Multiple LLMs** | Custo/benefício ruim | Fase 3+ |
| **Microservices** | Over-engineering | Nunca para esta escala |

### 6.2 Padrões a Evitar

| Padrão | Problema | Alternativa |
|--------|----------|-------------|
| **Otimização excessiva de parâmetros** | Overfitting | Poucos parâmetros robustos |
| **Backtesting sem walk-forward** | Viés de look-ahead | Sempre walk-forward |
| **Ignorar custos de transação** | P&L irreal | Incluir 0.25% por trade |
| **Trading durante leilão** | Slippage extremo | Esperar 5min pós-abertura |
| **Posições overnight sem stop** | Risco de gap | Sempre definir stop |
| **Confiar em uma fonte de dados** | Single point of failure | Redundância |
| **Deploy sem paper trading** | Bugs caros | Mínimo 5 dias paper |

### 6.3 Serviços Pagos Desnecessários para MVP

| Serviço | Custo típico | Por que não precisa |
|---------|--------------|---------------------|
| Bloomberg Terminal | $24k/ano | Overkill para VALE3 |
| Reuters Eikon | $15k/ano | Idem |
| AWS/GCP managed services | $200-500/mês | VPS simples basta |
| Dados tick-by-tick | $100-500/mês | 5min bars suficiente |
| Co-location | $1k+/mês | Não é HFT |
| Backtesting platforms (QuantConnect Pro) | $50-200/mês | Python local |

---

## 7. ROADMAP DETALHADO - 4 SEMANAS

### 7.1 Visão Geral

```
SEMANA 1          SEMANA 2          SEMANA 3          SEMANA 4
───────────────────────────────────────────────────────────────────►

┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│  INFRA  │      │ VALIDA- │      │ EXECUÇÃO│      │  TESTES │
│    +    │  ──► │   ÇÃO   │  ──► │    +    │  ──► │    +    │
│  DADOS  │      │  STAT   │      │  RISCO  │      │ GO-LIVE │
└─────────┘      └─────────┘      └─────────┘      └─────────┘

Entregáveis:     Entregáveis:     Entregáveis:     Entregáveis:
• Pipeline       • Granger test   • MT5 integrado  • Paper trading
• Database       • Backtest       • Stops impl.    • Dashboard
• Coleta auto    • GO/NO-GO       • Kill switches  • Go-live 10%
```

### 7.2 Semana 1: Infraestrutura e Dados

#### Dia 1-2: Setup Inicial

**Tarefas**:
- [ ] Criar repositório Git privado
- [ ] Setup ambiente Python (pyenv + venv)
- [ ] Estrutura de diretórios conforme seção 4.1
- [ ] Arquivo .env com credenciais (template)
- [ ] Instalar PostgreSQL + TimescaleDB (Docker)

**Entregável**: Ambiente de desenvolvimento funcional

#### Dia 3-4: Pipeline de Dados Minério

**Tarefas**:
- [ ] Implementar iron_ore_fetcher.py (Yahoo Finance)
- [ ] Implementar backup scraper (Investing.com)
- [ ] Testar coleta em diferentes horários
- [ ] Criar tabela prices_iron_ore no DB
- [ ] Scheduler para coleta a cada 5 minutos

**Entregável**: Coleta automática de minério funcionando

#### Dia 5: Pipeline de Dados VALE3

**Tarefas**:
- [ ] Conta na Clear ou XP (se não tiver)
- [ ] Instalar MT5 e configurar credenciais
- [ ] Implementar vale_fetcher.py
- [ ] Criar tabela prices_vale3 no DB
- [ ] Testar coleta durante pregão

**Entregável**: Coleta automática de VALE3 funcionando

#### Dia 6-7: Dados Auxiliares e Consolidação

**Tarefas**:
- [ ] Implementar auxiliary_fetcher.py (USD/BRL, VIX)
- [ ] Implementar data_validator.py
- [ ] Criar script de backfill histórico (6 meses)
- [ ] Notebook de análise exploratória inicial
- [ ] Documentar setup no README

**Entregável**: Pipeline completo com histórico

#### Checkpoint Semana 1

| Item | Critério de aceite |
|------|-------------------|
| Coleta minério | 24h sem falhas |
| Coleta VALE3 | Pregão completo sem falhas |
| Database | Dados consistentes, sem gaps >10min |
| Backfill | 6 meses de histórico disponível |

---

### 7.3 Semana 2: Validação Estatística

#### Dia 8-9: Features e Preparação

**Tarefas**:
- [ ] Implementar features.py
  - Retornos em múltiplas janelas
  - Volatilidade realizada
  - Z-score do movimento
- [ ] Alinhar timestamps entre mercados
- [ ] Criar dataset consolidado para análise
- [ ] Verificar qualidade dos dados

**Entregável**: Dataset pronto para testes estatísticos

#### Dia 10-11: Testes Estatísticos

**Tarefas**:
- [ ] Implementar validation.py
- [ ] Teste de correlação com lags (1h, 4h, 1d)
- [ ] Teste de Granger causality
- [ ] Teste de cointegração Johansen
- [ ] Análise por subperíodo (estabilidade)

**Entregável**: Notebook com resultados estatísticos

#### Dia 12-13: Backtest Walk-Forward

**Tarefas**:
- [ ] Implementar signal_generator.py (regras simples)
- [ ] Backtest com custos de transação
- [ ] Walk-forward: 60% treino / 20% val / 20% teste
- [ ] Calcular métricas: Sharpe, win rate, drawdown
- [ ] Sensitivity analysis nos thresholds

**Entregável**: Relatório de backtest com métricas

#### Dia 14: Decisão GO/NO-GO

**Tarefas**:
- [ ] Consolidar todos os resultados
- [ ] Documentar evidências
- [ ] Decisão formal GO/NO-GO
- [ ] Se GO: planejar semana 3
- [ ] Se NO-GO: documentar aprendizados

**Critérios GO**:
```
✅ Granger significativo (p < 0.05) em pelo menos 1 lag
✅ Correlação defasada > 0.3
✅ Sharpe ratio walk-forward > 1.0 após custos
✅ Win rate > 50%
✅ Max drawdown < 15% no backtest
```

**Critérios NO-GO**:
```
❌ Nenhuma significância estatística
❌ Sharpe < 0.5 após custos
❌ Resultados instáveis entre subperíodos
❌ Relação invertida (Vale lidera minério)
```

**Entregável**: Documento de decisão GO/NO-GO

---

### 7.4 Semana 3: Execução e Risco (se GO)

#### Dia 15-16: Integração MT5

**Tarefas**:
- [ ] Implementar mt5_connector.py
  - Conexão autenticada
  - Envio de ordens
  - Consulta de posições
  - Cancelamento de ordens
- [ ] Implementar order_manager.py
- [ ] Testes com conta demo
- [ ] Tratamento de erros e retries

**Entregável**: Execução de ordens funcional (demo)

#### Dia 17-18: Gestão de Risco

**Tarefas**:
- [ ] Implementar position_sizing.py
  - Método ATR-based
  - Limites de posição
- [ ] Implementar risk_limits.py
  - Daily loss limit
  - Exposure checks
- [ ] Implementar kill_switch.py
  - Todos os triggers
  - Ações automáticas

**Entregável**: Módulo de risco completo

#### Dia 19-20: Stops e Orquestração

**Tarefas**:
- [ ] Implementar lógica de stops
  - Stop inicial
  - Breakeven
  - Trailing stop
- [ ] Implementar state_machine.py
- [ ] Implementar main_loop.py
- [ ] Testes integrados end-to-end (demo)

**Entregável**: Sistema completo funcional (demo)

#### Dia 21: Alertas e Logs

**Tarefas**:
- [ ] Configurar Telegram Bot
- [ ] Implementar alerts.py
- [ ] Implementar logger.py
- [ ] Testar todos os alertas
- [ ] Verificar logs estão completos

**Entregável**: Sistema de alertas funcional

---

### 7.5 Semana 4: Testes e Go-Live

#### Dia 22-24: Paper Trading

**Tarefas**:
- [ ] Deploy em VPS (ou manter local)
- [ ] Iniciar paper trading (sem capital real)
- [ ] Monitorar 24/7
- [ ] Documentar todos os sinais gerados
- [ ] Verificar se comportamento = backtest

**Entregável**: 3 dias de paper trading sem erros

#### Dia 25-26: Dashboard e Documentação

**Tarefas**:
- [ ] Implementar dashboard.py (Streamlit simples)
- [ ] Criar manual de operações
- [ ] Documentar troubleshooting
- [ ] Criar checklists diários
- [ ] Treinar operação manual de emergência

**Entregável**: Dashboard funcional + documentação

#### Dia 27-28: Go-Live Gradual

**Tarefas**:
- [ ] Review final de segurança
- [ ] Transferir 10% do capital (R$2-5k)
- [ ] Primeiro trade real (se sinal)
- [ ] Monitoramento intensivo
- [ ] Documentar comportamento

**Entregável**: Sistema operacional com capital real

---

## 8. CUSTOS ESTIMADOS

### 8.1 Custos Mensais MVP

| Item | Custo (R$/mês) | Obrigatório? |
|------|----------------|--------------|
| VPS (2GB RAM, São Paulo) | 50-100 | SIM* |
| Domínio (se quiser) | 5 | NÃO |
| Telegram Bot | 0 | SIM |
| GitHub (private repo) | 0 | SIM |
| Dados minério | 0 | SIM |
| Dados VALE3 (MT5) | 0 | SIM |
| PostgreSQL (local/VPS) | 0 | SIM |
| **TOTAL** | **50-100** | |

*Pode rodar local inicialmente

### 8.2 Custos de Trading

| Item | Custo | Frequência |
|------|-------|------------|
| Corretagem (Clear) | R$0 | Por trade |
| Emolumentos B3 | ~0.03% | Por trade |
| ISS (se day trade SP) | 5% do lucro | Mensal |
| IR (swing trade) | 15% do lucro | Mensal |
| IR (day trade) | 20% do lucro | Mensal |

---

## 9. PRÓXIMOS PASSOS IMEDIATOS

### Hoje (Dia 0)

1. ☐ Criar repositório Git
2. ☐ Setup ambiente Python
3. ☐ Iniciar processo de conta na Clear (se não tiver)
4. ☐ Instalar Docker + PostgreSQL
5. ☐ Criar estrutura de diretórios

### Amanhã (Dia 1)

1. ☐ Implementar primeiro fetcher (Yahoo Finance)
2. ☐ Testar coleta de dados minério
3. ☐ Criar primeiras tabelas no database
4. ☐ Commit inicial no Git

### Esta Semana

1. ☐ Completar pipeline de dados
2. ☐ Backfill histórico 6 meses
3. ☐ Primeira análise exploratória

---

## 10. CHECKLIST FINAL PRÉ-GO-LIVE

### Checklist Técnico

```
□ Pipeline de dados rodando 48h sem falhas
□ Todos os testes unitários passando
□ Paper trading 5 dias sem erros
□ Kill switches todos testados
□ Alertas Telegram funcionando
□ Backup de database configurado
□ Logs sendo gravados corretamente
□ Dashboard mostrando métricas corretas
□ Documentação completa
□ Plano de rollback documentado
```

### Checklist de Risco

```
□ Position sizing validado
□ Stop loss implementado e testado
□ Daily loss limit implementado e testado
□ Kill switch manual testado
□ Drawdown alert configurado
□ Correlação monitoring ativo
□ Contato emergência corretora anotado
□ Credenciais backup armazenadas seguramente
```

### Checklist Operacional

```
□ Conta corretora com capital depositado
□ MT5 logado e conectado
□ VPS/máquina com uptime estável
□ Internet backup disponível
□ Celular com Telegram instalado
□ Checklist diário impresso
□ Manual de operações acessível
□ Segunda pessoa sabe operar (emergência)
```

---

**Status**: EM PLANEJAMENTO
