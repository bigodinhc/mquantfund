# Roadmap: Minerals Trading Quant Fund
## Sistema de Trading Quantitativo — Minério de Ferro × VALE3

**Versão:** 1.0  
**Data:** Janeiro 2026  
**Classificação:** Interno — Minerals Trading

---

## 1. Executive Summary

Este documento apresenta o roadmap completo para desenvolvimento do primeiro quant fund da Minerals Trading, explorando a hipótese de relação lead-lag entre futuros de minério de ferro (SGX/DCE) e VALE3.

### Premissas-Chave

| Dimensão | Definição |
|----------|-----------|
| **Objetivo** | Quant fund institucional da Minerals Trading |
| **Capital teste** | R$ 20.000 – 50.000 |
| **Infraestrutura** | Budget flexível (separado do capital de trading) |
| **Automação** | Fully automated (sem intervenção humana na execução) |
| **Disponibilidade** | Dedicação integral ao projeto |
| **Dados** | Acesso a Platts, LSEG Workspace e outras fontes pagas |

### Fases do Projeto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        VISÃO GERAL DAS FASES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FASE 1          FASE 2          FASE 3          FASE 4          FASE 5   │
│   ───────         ───────         ───────         ───────         ─────    │
│   Validação       Infraestrutura  Engine de       Produção        Escala   │
│   Estatística     & Data          Trading         Controlada                │
│                                                                             │
│   Semanas 1-2     Semanas 3-4     Semanas 5-7     Semanas 8-10    Sem 11+  │
│                                                                             │
│   ► Hipótese      ► Pipeline      ► Estratégia    ► Paper trade   ► +Ativos│
│   ► Go/No-Go      ► Database      ► Execução      ► Live 10%      ► +Estrat│
│   ► Backtest      ► APIs          ► Risk Mgmt     ► Ramp-up       ► Replic │
│                                                                             │
│   [GATE 1]        [GATE 2]        [GATE 3]        [GATE 4]                 │
│   Validação OK?   Dados OK?       Backtest OK?    Paper OK?                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura do Sistema

### 2.1 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    MINERALS QUANT FUND — ARQUITETURA GERAL                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CAMADA DE INGESTÃO                                  │   │
│  ├──────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                               │   │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      │   │
│  │   │   LSEG      │   │   Platts    │   │    MT5      │   │   Cedro     │      │   │
│  │   │  Workspace  │   │    API      │   │   (B3)      │   │  WebSocket  │      │   │
│  │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘      │   │
│  │          │                 │                 │                 │              │   │
│  │          └────────────────┬┴─────────────────┴─────────────────┘              │   │
│  │                           │                                                   │   │
│  │                           ▼                                                   │   │
│  │                 ┌─────────────────────┐                                       │   │
│  │                 │   DATA NORMALIZER   │                                       │   │
│  │                 │   (UTC alignment)   │                                       │   │
│  │                 └──────────┬──────────┘                                       │   │
│  │                            │                                                  │   │
│  └────────────────────────────┼──────────────────────────────────────────────────┘   │
│                               │                                                      │
│  ┌────────────────────────────┼──────────────────────────────────────────────────┐   │
│  │                            ▼                                                  │   │
│  │                 ┌─────────────────────┐                                       │   │
│  │                 │    TimescaleDB      │◄────── Dados históricos + real-time   │   │
│  │                 │    (PostgreSQL)     │                                       │   │
│  │                 └──────────┬──────────┘                                       │   │
│  │                            │                                                  │   │
│  │           CAMADA DE DADOS  │                                                  │   │
│  └────────────────────────────┼──────────────────────────────────────────────────┘   │
│                               │                                                      │
│  ┌────────────────────────────┼──────────────────────────────────────────────────┐   │
│  │                            ▼                                                  │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                      FEATURE ENGINE                                  │    │   │
│  │   ├─────────────────────────────────────────────────────────────────────┤    │   │
│  │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │   │
│  │   │  │   Retornos   │  │  Volatilidade│  │  Correlação  │              │    │   │
│  │   │  │   Minério    │  │    ATR/σ     │  │   Rolling    │              │    │   │
│  │   │  └──────────────┘  └──────────────┘  └──────────────┘              │    │   │
│  │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │   │
│  │   │  │   USD/BRL    │  │     VIX      │  │   Spread     │              │    │   │
│  │   │  │   Features   │  │   Regime     │  │   SGX-DCE    │              │    │   │
│  │   │  └──────────────┘  └──────────────┘  └──────────────┘              │    │   │
│  │   └──────────────────────────────┬──────────────────────────────────────┘    │   │
│  │                                  │                                           │   │
│  │           CAMADA DE PROCESSAMENTO│                                           │   │
│  └──────────────────────────────────┼───────────────────────────────────────────┘   │
│                                     │                                               │
│  ┌──────────────────────────────────┼───────────────────────────────────────────┐   │
│  │                                  ▼                                           │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                      STRATEGY ENGINE                                 │    │   │
│  │   ├─────────────────────────────────────────────────────────────────────┤    │   │
│  │   │                                                                      │    │   │
│  │   │   ┌────────────────┐      ┌────────────────┐                        │    │   │
│  │   │   │  RULE-BASED    │      │   ML-BASED     │                        │    │   │
│  │   │   │  (Estratégia 1)│      │  (Estratégia 2)│                        │    │   │
│  │   │   │                │      │                │                        │    │   │
│  │   │   │  • Limiares σ  │      │  • XGBoost     │                        │    │   │
│  │   │   │  • Filtros     │      │  • Walk-forward│                        │    │   │
│  │   │   │  • Confirmação │      │  • Retreino    │                        │    │   │
│  │   │   └───────┬────────┘      └───────┬────────┘                        │    │   │
│  │   │           │                       │                                 │    │   │
│  │   │           └───────────┬───────────┘                                 │    │   │
│  │   │                       │                                             │    │   │
│  │   │                       ▼                                             │    │   │
│  │   │            ┌─────────────────────┐                                  │    │   │
│  │   │            │   SIGNAL COMBINER   │                                  │    │   │
│  │   │            │   (Ensemble/Vote)   │                                  │    │   │
│  │   │            └──────────┬──────────┘                                  │    │   │
│  │   │                       │                                             │    │   │
│  │   └───────────────────────┼─────────────────────────────────────────────┘    │   │
│  │                           │                                                  │   │
│  │           CAMADA DE ESTRATÉGIA                                               │   │
│  └───────────────────────────┼──────────────────────────────────────────────────┘   │
│                              │                                                      │
│  ┌───────────────────────────┼──────────────────────────────────────────────────┐   │
│  │                           ▼                                                  │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                       RISK ENGINE                                    │    │   │
│  │   ├─────────────────────────────────────────────────────────────────────┤    │   │
│  │   │                                                                      │    │   │
│  │   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │   │
│  │   │   │  Position    │  │    Stop      │  │    Loss      │              │    │   │
│  │   │   │   Sizing     │  │   Manager    │  │   Limits     │              │    │   │
│  │   │   │  (ATR-based) │  │  (Trailing)  │  │  (Cascading) │              │    │   │
│  │   │   └──────────────┘  └──────────────┘  └──────────────┘              │    │   │
│  │   │                                                                      │    │   │
│  │   │   ┌──────────────────────────────────────────────────┐              │    │   │
│  │   │   │              KILL SWITCH HIERARCHY               │              │    │   │
│  │   │   │   L1: Auto │ L2: Confirm │ L3: Manual │ L4: Panic│              │    │   │
│  │   │   └──────────────────────────────────────────────────┘              │    │   │
│  │   │                       │                                             │    │   │
│  │   └───────────────────────┼─────────────────────────────────────────────┘    │   │
│  │                           │                                                  │   │
│  │           CAMADA DE RISCO │                                                  │   │
│  └───────────────────────────┼──────────────────────────────────────────────────┘   │
│                              │                                                      │
│  ┌───────────────────────────┼──────────────────────────────────────────────────┐   │
│  │                           ▼                                                  │   │
│  │   ┌─────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                    EXECUTION ENGINE                                  │    │   │
│  │   ├─────────────────────────────────────────────────────────────────────┤    │   │
│  │   │                                                                      │    │   │
│  │   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │    │   │
│  │   │   │   Order      │  │   Broker     │  │   Fill       │              │    │   │
│  │   │   │  Generator   │  │   Router     │  │  Tracker     │              │    │   │
│  │   │   │              │  │  (MT5/Cedro) │  │              │              │    │   │
│  │   │   └──────────────┘  └──────────────┘  └──────────────┘              │    │   │
│  │   │                                                                      │    │   │
│  │   └─────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                              │   │
│  │           CAMADA DE EXECUÇÃO                                                 │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CAMADA DE OBSERVABILIDADE                          │   │
│  ├──────────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                               │   │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │   │   Grafana    │  │   Alertas    │  │    Logs      │  │   Audit      │     │   │
│  │   │  Dashboard   │  │  Telegram    │  │  Estruturado │  │   Trail      │     │   │
│  │   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  │                                                                               │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fluxo de Dados Real-Time

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE DADOS — CICLO DE TRADING                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   00:00 UTC          06:00 UTC          12:00 UTC          18:00 UTC        │
│      │                  │                  │                  │             │
│      │   DCE Session    │                  │                  │             │
│      │ ◄───────────────►│                  │                  │             │
│      │   01:00-07:00    │                  │                  │             │
│      │                  │                  │                  │             │
│      │         SGX T-Session               │                  │             │
│      │◄────────────────────────────────────►                  │             │
│      │        23:25(D-1) - 12:00           │                  │             │
│      │                  │                  │                  │             │
│      │                  │         SGX T+1 Session             │             │
│      │                  │         ◄────────────────────────────►            │
│      │                  │          12:15 - 20:45              │             │
│      │                  │                  │                  │             │
│      │                  │         B3 Session                  │             │
│      │                  │         ◄────────────────────────────►            │
│      │                  │          13:00 - 20:55              │             │
│      │                  │                  │                  │             │
│      ▼                  ▼                  ▼                  ▼             │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     TIMELINE DE DECISÃO                              │   │
│   ├─────────────────────────────────────────────────────────────────────┤   │
│   │                                                                      │   │
│   │  12:00 UTC          12:30 UTC          13:00 UTC          13:30 UTC │   │
│   │     │                  │                  │                  │       │   │
│   │     ▼                  ▼                  ▼                  ▼       │   │
│   │  ┌───────┐         ┌───────┐         ┌───────┐         ┌───────┐   │   │
│   │  │ SGX   │────────►│Feature│────────►│ B3    │────────►│Execute│   │   │
│   │  │ Close │         │ Calc  │         │ Open  │         │ Order │   │   │
│   │  └───────┘         └───────┘         └───────┘         └───────┘   │   │
│   │                                                                      │   │
│   │  • Captura         • Retornos        • Confirma        • Submete    │   │
│   │    preço final     • Volatilidade      sinal             ordem      │   │
│   │  • Gera sinal      • Correlação      • Verifica        • Monitora   │   │
│   │    preliminar      • Risk check        liquidez          fill       │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológica

### 3.1 Decisões de Stack — Recomendado vs Alternativas

| Componente | Escolha Recomendada | Alternativa | Justificativa |
|------------|---------------------|-------------|---------------|
| **Linguagem principal** | Python 3.11+ | - | Ecossistema quant maduro, bibliotecas, sua experiência |
| **Database time-series** | TimescaleDB | InfluxDB, QuestDB | PostgreSQL-compatible, compression, chunks automáticos |
| **Message queue** | Redis Streams | RabbitMQ | Simplicidade, pub/sub nativo, já resolve o problema |
| **Dados minério** | LSEG Workspace API | Platts, MetalpriceAPI | Você já tem acesso, dados oficiais |
| **Dados VALE3** | Cedro WebSocket | MT5 via Clear | Baixa latência, profissional, dados tick-by-tick |
| **Broker B3** | Clear (MT5) + Cedro | XP, BTG | Zero corretagem, API madura, redundância |
| **Orquestração** | Prefect | Airflow, Dagster | Python-native, observabilidade built-in, cloud grátis |
| **Monitoramento** | Grafana + Prometheus | Datadog | Self-hosted, custo zero, dashboards flexíveis |
| **Alertas** | Telegram Bot | Discord, SMS | Real-time, grátis, você já usa |
| **Infraestrutura** | VPS São Paulo (Vultr) | AWS, GCP | Latência B3, custo previsível, simplicidade |
| **Versionamento** | Git + GitHub | GitLab | Standard, CI/CD integrado |
| **CI/CD** | GitHub Actions | Jenkins | Integrado ao repo, gratuito para repos privados |
| **Containerização** | Docker + Docker Compose | K8s | Escala não justifica K8s ainda |

### 3.2 Stack Detalhada por Camada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STACK COMPLETA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  CAMADA              TECNOLOGIA              VERSÃO         PROPÓSITO       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                              │
│  INGESTÃO            LSEG Workspace API      -              Minério SGX/DCE │
│                      Cedro Market Data       WebSocket      VALE3 L1/L2     │
│                      MT5 Python API          5.0.45+        Backup + exec   │
│                      yfinance                0.2+           USD/BRL, VIX    │
│                                                                              │
│  PROCESSAMENTO       Python                  3.11+          Core language   │
│                      Pandas                  2.0+           Data wrangling  │
│                      NumPy                   1.24+          Numerics        │
│                      SciPy                   1.11+          Statistics      │
│                      statsmodels             0.14+          Granger, VAR    │
│                      arch                    6.0+           GARCH models    │
│                                                                              │
│  ML/ESTRATÉGIA       scikit-learn            1.3+           Baseline ML     │
│                      XGBoost                 2.0+           Gradient boost  │
│                      LightGBM                4.0+           Alternativa     │
│                      Optuna                  3.3+           Hyperparameter  │
│                                                                              │
│  PERSISTÊNCIA        TimescaleDB             2.13+          Time-series     │
│                      Redis                   7.0+           Cache + queue   │
│                      SQLAlchemy              2.0+           ORM             │
│                                                                              │
│  ORQUESTRAÇÃO        Prefect                 2.14+          Workflow engine │
│                      APScheduler             3.10+          Jobs simples    │
│                                                                              │
│  EXECUÇÃO            MT5 Python              5.0.45+        Orders B3       │
│                      Cedro OMS               API            Alternativa     │
│                                                                              │
│  OBSERVABILIDADE     Grafana                 10.0+          Dashboards      │
│                      Prometheus              2.47+          Métricas        │
│                      Loki                    2.9+           Logs            │
│                      structlog               23.0+          Structured log  │
│                                                                              │
│  ALERTAS             python-telegram-bot     20.0+          Notificações    │
│                                                                              │
│  INFRA               Docker                  24.0+          Containers      │
│                      Docker Compose          2.21+          Orquestração    │
│                      Vultr VPS               -              Hosting         │
│                      Ubuntu Server           22.04 LTS      OS              │
│                                                                              │
│  DEV                 Poetry                  1.6+           Dependency mgmt │
│                      pytest                  7.4+           Testing         │
│                      black + ruff            -              Linting         │
│                      pre-commit              3.5+           Git hooks       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 O Que NÃO Usar (e Por Quê)

| Tecnologia | Por que evitar | Quando reconsiderar |
|------------|----------------|---------------------|
| **Kubernetes** | Over-engineering para 1-2 containers; complexidade de manutenção | Se escalar para 10+ estratégias independentes |
| **Apache Kafka** | Overkill para volume de mensagens esperado; Redis Streams resolve | Se processar 100k+ eventos/segundo |
| **Airflow** | Muito pesado para workflows simples; DAGs verbose | Se integrar com ecossistema de data engineering maior |
| **MongoDB** | Time-series não é forte; schemas flexíveis não necessários | Nunca para este caso de uso |
| **AWS Lambda** | Cold start prejudica latência; custo imprevisível | Se precisar de burst compute para ML training |
| **LLMs para sinais** | Latência proibitiva; alucinação; custo alto | Apenas para sumarização/alertas, nunca para sinais |
| **C++/Rust** | Latência de ms não justifica complexidade; não é HFT | Se migrar para estratégias sub-segundo |
| **Microservices** | Overhead de comunicação; complexidade desnecessária | Se equipe crescer para 5+ devs |
| **Terraform** | Infra simples demais; VPS único | Se multi-cloud ou infra complexa |

---

## 4. Estrutura do Projeto

### 4.1 Estrutura de Diretórios

```
minerals-quant-fund/
│
├── README.md                          # Documentação principal
├── pyproject.toml                     # Poetry config + dependencies
├── poetry.lock                        # Lock file
├── docker-compose.yml                 # Orquestração local
├── docker-compose.prod.yml            # Produção
├── Makefile                           # Comandos úteis
├── .env.example                       # Template de variáveis
├── .pre-commit-config.yaml            # Git hooks
│
├── docs/                              # Documentação
│   ├── architecture.md                # Decisões de arquitetura
│   ├── runbook.md                     # Operações diárias
│   ├── incident-response.md           # Playbook de incidentes
│   └── research/                      # Notebooks de pesquisa
│       ├── 01_exploratory_analysis.ipynb
│       ├── 02_granger_causality.ipynb
│       ├── 03_cointegration.ipynb
│       └── 04_backtest_results.ipynb
│
├── src/
│   └── minerals_quant/
│       ├── __init__.py
│       │
│       ├── config/                    # Configuração centralizada
│       │   ├── __init__.py
│       │   ├── settings.py            # Pydantic settings
│       │   └── constants.py           # Constantes do sistema
│       │
│       ├── data/                      # Camada de ingestão
│       │   ├── __init__.py
│       │   ├── base.py                # Interface abstrata
│       │   ├── lseg_client.py         # LSEG Workspace API
│       │   ├── cedro_client.py        # Cedro WebSocket
│       │   ├── mt5_client.py          # MetaTrader 5
│       │   ├── market_data.py         # yfinance, etc
│       │   └── normalizer.py          # Alinhamento UTC
│       │
│       ├── features/                  # Feature engineering
│       │   ├── __init__.py
│       │   ├── base.py                # Interface abstrata
│       │   ├── returns.py             # Cálculo de retornos
│       │   ├── volatility.py          # ATR, σ, GARCH
│       │   ├── correlation.py         # Rolling correlation
│       │   ├── regime.py              # Detecção de regime
│       │   └── pipeline.py            # Feature pipeline
│       │
│       ├── strategy/                  # Estratégias de trading
│       │   ├── __init__.py
│       │   ├── base.py                # Interface abstrata
│       │   ├── rule_based.py          # Estratégia 1: regras
│       │   ├── ml_based.py            # Estratégia 2: ML
│       │   ├── ensemble.py            # Combinador de sinais
│       │   └── backtest/              # Backtesting engine
│       │       ├── __init__.py
│       │       ├── engine.py          # Core backtest
│       │       ├── metrics.py         # Sharpe, Sortino, etc
│       │       └── walk_forward.py    # Walk-forward validation
│       │
│       ├── risk/                      # Gestão de risco
│       │   ├── __init__.py
│       │   ├── position_sizing.py     # ATR-based sizing
│       │   ├── stop_manager.py        # Stop loss/trailing
│       │   ├── limits.py              # Loss limits cascading
│       │   └── kill_switch.py         # Circuit breakers
│       │
│       ├── execution/                 # Execução de ordens
│       │   ├── __init__.py
│       │   ├── base.py                # Interface abstrata
│       │   ├── order_generator.py     # Cria ordens
│       │   ├── mt5_executor.py        # Execução via MT5
│       │   ├── cedro_executor.py      # Execução via Cedro
│       │   └── paper_trader.py        # Paper trading mode
│       │
│       ├── monitoring/                # Observabilidade
│       │   ├── __init__.py
│       │   ├── metrics.py             # Prometheus metrics
│       │   ├── alerts.py              # Telegram alerts
│       │   ├── logger.py              # Structured logging
│       │   └── dashboard.py           # Grafana config
│       │
│       ├── db/                        # Persistência
│       │   ├── __init__.py
│       │   ├── models.py              # SQLAlchemy models
│       │   ├── repository.py          # Data access layer
│       │   └── migrations/            # Alembic migrations
│       │
│       └── orchestration/             # Workflows
│           ├── __init__.py
│           ├── flows.py               # Prefect flows
│           └── tasks.py               # Prefect tasks
│
├── scripts/                           # Scripts utilitários
│   ├── setup_database.py              # Inicialização DB
│   ├── backfill_data.py               # Carga histórica
│   ├── validate_hypothesis.py         # Validação estatística
│   └── deploy.sh                      # Deploy script
│
├── tests/                             # Testes
│   ├── conftest.py                    # Fixtures pytest
│   ├── unit/                          # Testes unitários
│   ├── integration/                   # Testes integração
│   └── e2e/                           # Testes end-to-end
│
├── infrastructure/                    # Infra as code
│   ├── docker/
│   │   ├── Dockerfile                 # App container
│   │   ├── Dockerfile.dev             # Dev container
│   │   └── grafana/
│   │       └── dashboards/            # Dashboard JSON
│   └── prometheus/
│       └── prometheus.yml             # Config
│
└── notebooks/                         # Jupyter notebooks
    ├── research/                      # Análises ad-hoc
    └── reports/                       # Relatórios
```

### 4.2 Hierarquia de Componentes e Dependências

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HIERARQUIA DE DEPENDÊNCIAS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              ┌──────────────┐                               │
│                              │   CONFIG     │                               │
│                              │  (settings)  │                               │
│                              └──────┬───────┘                               │
│                                     │                                        │
│                    ┌────────────────┼────────────────┐                      │
│                    │                │                │                      │
│                    ▼                ▼                ▼                      │
│             ┌──────────┐     ┌──────────┐     ┌──────────┐                  │
│             │   DATA   │     │    DB    │     │MONITORING│                  │
│             │ (clients)│     │ (models) │     │ (metrics)│                  │
│             └────┬─────┘     └────┬─────┘     └────┬─────┘                  │
│                  │                │                │                        │
│                  └────────────────┼────────────────┘                        │
│                                   │                                         │
│                                   ▼                                         │
│                            ┌──────────────┐                                 │
│                            │   FEATURES   │                                 │
│                            │  (pipeline)  │                                 │
│                            └──────┬───────┘                                 │
│                                   │                                         │
│                    ┌──────────────┼──────────────┐                          │
│                    │              │              │                          │
│                    ▼              ▼              ▼                          │
│             ┌──────────┐   ┌──────────┐   ┌──────────┐                      │
│             │ STRATEGY │   │   RISK   │   │EXECUTION │                      │
│             │(signals) │   │(sizing)  │   │ (orders) │                      │
│             └────┬─────┘   └────┬─────┘   └────┬─────┘                      │
│                  │              │              │                            │
│                  └──────────────┼──────────────┘                            │
│                                 │                                           │
│                                 ▼                                           │
│                          ┌──────────────┐                                   │
│                          │ORCHESTRATION │                                   │
│                          │   (flows)    │                                   │
│                          └──────────────┘                                   │
│                                                                              │
│  REGRA: Dependências sempre fluem para BAIXO                                │
│  • config não depende de nada                                               │
│  • data/db/monitoring dependem apenas de config                             │
│  • features depende de data e db                                            │
│  • strategy/risk/execution dependem de features                             │
│  • orchestration orquestra tudo                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Cronograma Detalhado

### 5.1 Visão Macro (10 Semanas até Produção Controlada)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CRONOGRAMA MACRO                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEMANA     1    2    3    4    5    6    7    8    9    10   11   12      │
│             │    │    │    │    │    │    │    │    │    │    │    │       │
│  FASE 1     ████████                                                        │
│  Validação  │    │                                                          │
│             │    └─► GATE 1: Hipótese válida?                               │
│                                                                              │
│  FASE 2          ████████                                                   │
│  Infra                │    │                                                │
│                       │    └─► GATE 2: Pipeline estável?                    │
│                                                                              │
│  FASE 3                    ████████████                                     │
│  Engine                         │    │    │                                 │
│                                 │    │    └─► GATE 3: Backtest positivo?   │
│                                                                              │
│  FASE 4                                   ████████████                      │
│  Produção                                      │    │    │                  │
│                                                │    │    └─► GATE 4: Paper OK│
│                                                                              │
│  FASE 5                                                  ████████────►      │
│  Escala                                                       │             │
│                                                               └─► Live      │
│                                                                              │
│  LEGENDA:  ████ = Desenvolvimento ativo                                     │
│            ─► = Gate de decisão                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Fase 1: Validação Estatística (Semanas 1-2)

**Objetivo**: Validar ou refutar a hipótese de lead-lag antes de investir em infraestrutura.

#### Semana 1: Setup + Análise Exploratória

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1 | Setup ambiente Python + Jupyter | pyproject.toml configurado | Poetry install sem erros |
| 1-2 | Extração dados históricos LSEG | Dataset minério SGX 2+ anos | Dados sem gaps críticos |
| 2-3 | Extração dados históricos VALE3 | Dataset VALE3 2+ anos | Alinhamento temporal OK |
| 3-4 | Alinhamento temporal UTC | Dataset unificado | Timestamps consistentes |
| 4-5 | Análise exploratória | Notebook com visualizações | Correlação descritiva >0.3 |

**Entregáveis Semana 1**:
- `notebooks/research/01_exploratory_analysis.ipynb`
- Dataset limpo em `/data/processed/`
- Documentação de tratamento de dados

#### Semana 2: Validação Estatística Rigorosa

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | Teste de Granger Causality | Notebook com resultados | p-value < 0.05 em 2+ lags |
| 2-3 | Análise de Cointegração Johansen | Resultados documentados | Vetor cointegrador significativo |
| 3-4 | Walk-forward backtest preliminar | Sharpe ratio estimado | Sharpe > 0.8 após custos |
| 4-5 | Documentação e decisão Go/No-Go | Relatório de validação | Critérios de gate atendidos |

**GATE 1 — Critérios de Go**:
- [ ] Granger causality significativa (p < 0.05) em pelo menos 2 janelas de lag
- [ ] Correlação defasada > 0.3 consistente em múltiplos subperíodos
- [ ] Walk-forward backtest com Sharpe > 0.8 (após custos de 0.25%)
- [ ] Relação estável em pelo menos 3 regimes diferentes (pré-COVID, COVID, pós-COVID)

**GATE 1 — Critérios de No-Go**:
- [ ] Nenhuma significância estatística em qualquer lag
- [ ] Sharpe < 0.5 após custos
- [ ] Relação inverte direção entre subperíodos

**Ação se No-Go**: Documentar aprendizados, pivotar para hipóteses alternativas (outros pares de ativos), ou arquivar projeto.

### 5.3 Fase 2: Infraestrutura e Pipeline de Dados (Semanas 3-4)

**Objetivo**: Construir pipeline de dados robusto e confiável.

#### Semana 3: Core Infrastructure

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1 | Setup VPS Vultr São Paulo | VPS rodando Ubuntu 22.04 | SSH funcionando, firewall configurado |
| 1-2 | Docker + Docker Compose | Containers base | `docker-compose up` sem erros |
| 2-3 | TimescaleDB setup | Database rodando | Hypertables criados |
| 3-4 | Cliente LSEG Workspace | `lseg_client.py` | Dados minério em real-time |
| 4-5 | Cliente Cedro WebSocket | `cedro_client.py` | Dados VALE3 tick-by-tick |

#### Semana 4: Pipeline Completo

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | Data normalizer UTC | `normalizer.py` | Todos timestamps UTC |
| 2-3 | Feature pipeline | `features/pipeline.py` | Features calculando corretamente |
| 3-4 | Backfill histórico | Script de carga | 2+ anos de dados no DB |
| 4-5 | Monitoring básico | Grafana + métricas | Dashboard de saúde do pipeline |

**GATE 2 — Critérios de Go**:
- [ ] Pipeline rodando 48h sem falhas
- [ ] Latência de dados < 5 minutos consistentemente
- [ ] Dados históricos carregados e validados
- [ ] Monitoramento alertando corretamente em falhas simuladas

### 5.4 Fase 3: Trading Engine (Semanas 5-7)

**Objetivo**: Implementar estratégias, backtesting robusto e gestão de risco.

#### Semana 5: Estratégia Rule-Based

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | Implementar Estratégia 1 | `strategy/rule_based.py` | Sinais gerando corretamente |
| 2-3 | Backtest engine | `backtest/engine.py` | Resultados reproduzíveis |
| 3-4 | Métricas de performance | `backtest/metrics.py` | Sharpe, Sortino, Max DD |
| 4-5 | Walk-forward validation | `backtest/walk_forward.py` | Validação out-of-sample |

#### Semana 6: Estratégia ML + Risk Management

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | Implementar Estratégia 2 (XGBoost) | `strategy/ml_based.py` | Modelo treinando |
| 2-3 | Hyperparameter tuning (Optuna) | Melhores parâmetros | Cross-validation OK |
| 3-4 | Position sizing ATR-based | `risk/position_sizing.py` | Sizing dinâmico |
| 4-5 | Stop manager | `risk/stop_manager.py` | Trailing stops funcionando |

#### Semana 7: Kill Switches + Ensemble

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | Loss limits cascading | `risk/limits.py` | Limites enforced |
| 2-3 | Kill switch hierarchy | `risk/kill_switch.py` | Todos níveis testados |
| 3-4 | Ensemble de estratégias | `strategy/ensemble.py` | Combinação funcionando |
| 4-5 | Backtest final integrado | Relatório completo | Sharpe > 1.0 após custos |

**GATE 3 — Critérios de Go**:
- [ ] Backtest walk-forward com Sharpe > 1.0 após custos
- [ ] Deflated Sharpe Ratio > 0.8 (ajustado para múltiplos testes)
- [ ] Max drawdown histórico < 15%
- [ ] Kill switches testados e funcionando
- [ ] Performance similar em múltiplos regimes

### 5.5 Fase 4: Produção Controlada (Semanas 8-10)

**Objetivo**: Paper trading extensivo seguido de live trading com capital mínimo.

#### Semana 8: Execution Engine

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-2 | MT5 executor | `execution/mt5_executor.py` | Ordens executando |
| 2-3 | Paper trader mode | `execution/paper_trader.py` | Simulação realista |
| 3-4 | Order generator | `execution/order_generator.py` | Ordens corretas |
| 4-5 | Reconciliação | Script de reconciliação | Posições batendo |

#### Semana 9: Paper Trading Intensivo

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1-5 | Paper trading 5 dias | Log de trades | Zero erros técnicos |
| Contínuo | Monitoramento | Dashboards | Alertas funcionando |
| Contínuo | Ajustes finos | Bug fixes | Sistema estável |

#### Semana 10: Go-Live Controlado

| Dia | Atividade | Entregável | Critério de Sucesso |
|-----|-----------|------------|---------------------|
| 1 | Deploy produção | Sistema live | Health checks OK |
| 2 | Live com 10% capital (R$2-5k) | Primeiros trades reais | Execução correta |
| 3-5 | Monitoramento intensivo | Relatórios diários | Performance conforme esperado |

**GATE 4 — Critérios de Go para Ramp-Up**:
- [ ] 5 dias de paper trading sem erros técnicos
- [ ] Performance paper trading dentro de ±20% do backtest
- [ ] Zero triggers de kill switch durante paper
- [ ] Reconciliação perfeita (posições = extrato corretora)

**Ramp-Up de Capital**:
- Semana 10: 10% (R$2-5k)
- Semana 12: 25% (R$5-12.5k) — se performance OK
- Semana 14: 50% (R$10-25k) — se performance OK
- Semana 16+: 100% (R$20-50k) — se performance OK

### 5.6 Fase 5: Escala e Evolução (Semana 11+)

| Horizonte | Iniciativa | Pré-requisito |
|-----------|------------|---------------|
| Mês 3 | Adicionar segundo ativo (CSN, Usiminas) | Sistema estável por 30 dias |
| Mês 4 | Implementar Estratégia 3 (NLP) | Alpha positivo consistente |
| Mês 6 | Considerar outros mercados (BHP, RIO) | Validação em múltiplos ativos BR |
| Mês 12 | Replicar para outros clientes Minerals | Track record documentado |

---

## 6. Orçamento e Recursos

### 6.1 Custos de Infraestrutura (Mensal)

| Item | Custo Mensal | Notas |
|------|--------------|-------|
| VPS Vultr São Paulo (4 vCPU, 8GB RAM) | R$ 300-400 | High Frequency compute |
| TimescaleDB (self-hosted no VPS) | R$ 0 | Incluso no VPS |
| Redis (self-hosted) | R$ 0 | Incluso no VPS |
| Grafana Cloud (free tier) | R$ 0 | Até 10k métricas |
| GitHub (private repos) | R$ 0 | Free tier suficiente |
| Telegram Bot | R$ 0 | Gratuito |
| LSEG Workspace | Já contratado | Minerals Trading |
| Cedro Market Data | R$ 200-500 | Negociar com corretora |
| Clear/XP (corretagem) | R$ 0 | Zero corretagem |
| **Total Infraestrutura** | **R$ 500-900/mês** | |

### 6.2 Custos de Desenvolvimento (One-Time)

| Item | Custo | Notas |
|------|-------|-------|
| Seu tempo (10 semanas × 40h) | — | Custo de oportunidade |
| Licenças software | R$ 0 | Tudo open-source |
| Dados históricos adicionais | R$ 0-2.000 | Se precisar além do LSEG |
| **Total Setup** | **R$ 0-2.000** | |

### 6.3 Capital de Trading

| Fase | Capital em Risco | Risco Máximo (20% DD) |
|------|------------------|----------------------|
| Paper Trading | R$ 0 | R$ 0 |
| Live 10% | R$ 2.000-5.000 | R$ 400-1.000 |
| Live 25% | R$ 5.000-12.500 | R$ 1.000-2.500 |
| Live 50% | R$ 10.000-25.000 | R$ 2.000-5.000 |
| Live 100% | R$ 20.000-50.000 | R$ 4.000-10.000 |

---

## 7. Riscos e Mitigações

### 7.1 Matriz de Riscos do Projeto

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Validação estatística negativa (Fase 1) | MÉDIA | CRÍTICO | Gate claro; pivot rápido |
| Dados LSEG insuficientes | BAIXA | ALTO | Alternativas mapeadas (Platts, SGX direto) |
| API Cedro instável | MÉDIA | MÉDIO | MT5 como backup; redundância |
| Overfitting no backtest | ALTA | ALTO | Walk-forward; Deflated Sharpe; holdout set |
| Bug em produção causa perda | MÉDIA | ALTO | Paper trading extensivo; capital mínimo inicial |
| Correlação colapsa pós-deploy | MÉDIA | ALTO | Monitoramento de correlação; auto-pause |
| Evento Vale (Brumadinho-like) | BAIXA | CRÍTICO | Position limits; stops (com gap risk); diversificação futura |

### 7.2 Critérios de Sunset (Quando Abandonar)

| Trigger | Ação |
|---------|------|
| Gate 1 falha (validação negativa) | Pivotar ou arquivar |
| 3 meses consecutivos sem retorno positivo | Pause + revalidação completa |
| Drawdown > 20% | Full stop + investigação |
| Correlação minério-VALE3 < 0.2 por 10 dias | Auto-pause + revalidação |
| Sharpe rolling 90 dias < 0.5 | Reduzir capital 50% + investigar |

---

## 8. Checklist de Go-Live

### Pré-Requisitos Técnicos

- [ ] VPS provisionado e configurado
- [ ] Todos containers Docker rodando
- [ ] TimescaleDB com dados históricos carregados
- [ ] Pipeline de dados real-time estável por 48h+
- [ ] Feature engine calculando corretamente
- [ ] Estratégias backtestadas com resultados documentados
- [ ] Risk engine com todos limites configurados
- [ ] Kill switches testados em todos cenários
- [ ] Execution engine conectado à corretora
- [ ] Paper trading por 5+ dias sem erros
- [ ] Monitoring e alertas funcionando
- [ ] Runbook operacional documentado
- [ ] Processo de reconciliação validado

### Pré-Requisitos Operacionais

- [ ] Conta na corretora ativa e com capital
- [ ] Contatos de emergência documentados
- [ ] Calendário de feriados (BR, SG, CN) configurado
- [ ] Backup de credenciais em local seguro
- [ ] Plano de contingência para falhas críticas

### Pré-Requisitos de Negócio

- [ ] Aprovação interna Minerals Trading
- [ ] Documentação de compliance (se aplicável)
- [ ] Acordo sobre ramp-up de capital
- [ ] Definição de métricas de sucesso

---

## 9. Próximos Passos Imediatos

### Esta Semana

1. **Dia 1-2**: Setup ambiente de desenvolvimento
   - Criar repositório GitHub
   - Configurar Poetry com dependências base
   - Setup Jupyter para análise
   
2. **Dia 2-3**: Extração de dados LSEG
   - Conectar à API do Workspace
   - Exportar série histórica minério SGX (2+ anos)
   - Documentar estrutura dos dados

3. **Dia 3-4**: Extração dados VALE3
   - Via yfinance para histórico
   - Documentar gaps e ajustes

4. **Dia 4-5**: Primeira análise exploratória
   - Correlação defasada
   - Visualizações básicas
   - Identificar padrões iniciais

### Decisões Pendentes

| Decisão | Opções | Deadline | Responsável |
|---------|--------|----------|-------------|
| Corretora principal | Clear vs XP | Fim semana 1 | Bigode |
| Fonte primária minério | LSEG vs Platts | Durante análise | Bigode |
| Hospedagem VPS | Vultr vs DigitalOcean | Início semana 3 | Bigode |

---

## 10. Apêndices

### A. Referências Técnicas

- [TimescaleDB Docs](https://docs.timescale.com/)
- [Prefect Docs](https://docs.prefect.io/)
- [MT5 Python API](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [statsmodels - Granger Causality](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.grangercausalitytests.html)

### B. Glossário

| Termo | Definição |
|-------|-----------|
| **Lead-lag** | Relação onde variável X antecipa movimentos de Y |
| **Walk-forward** | Validação com retreino progressivo |
| **ATR** | Average True Range — medida de volatilidade |
| **Sharpe Ratio** | Retorno ajustado ao risco (retorno / volatilidade) |
| **Drawdown** | Perda máxima do pico ao vale |
| **Kill switch** | Mecanismo de parada automática de emergência |

### C. Contatos e Recursos

| Recurso | Contato/Link |
|---------|--------------|
| Suporte Cedro | [A definir] |
| Suporte Clear/XP | [A definir] |
| Emergência corretora | [A definir] |
| LSEG Workspace | [Acesso Minerals] |

---

**Documento preparado para:** Minerals Trading  
**Versão:** 1.0  
**Última atualização:** Janeiro 2026
