# ROADMAP CONSOLIDADO: Fundo Quant VALE3/Minério de Ferro
## Sistema de Trading Quantitativo — MVP 4 Semanas

**Versão**: 3.0 (Consolidada + Stack Simplificada)
**Data**: Janeiro 2026
**Capital**: R$ 20.000 – 50.000
**Horizonte MVP**: 4 semanas até operação com capital real (10%)
**Stack**: Supabase + Railway + GitHub + Clear (MT5)

---

## AVISO CRÍTICO: HIPÓTESE NÃO VALIDADA

> **A relação lead-lag entre futuros de minério de ferro e VALE3 é uma HIPÓTESE, não um fato estabelecido.** Pesquisa acadêmica não encontrou estudos peer-reviewed específicos sobre esta relação preditiva. A implementação deve ser precedida de validação estatística rigorosa, e o projeto pode ser descontinuado na Semana 2 se os dados não suportarem a hipótese.

---

## A. FORMULAÇÃO DA HIPÓTESE E VALIDAÇÃO

### A.1 Definição Formal da Hipótese

**Hipótese Principal (H₁)**: Variações significativas nos preços de futuros de minério de ferro na sessão asiática (SGX/DCE) contêm informação preditiva para retornos de VALE3 no pregão brasileiro seguinte.

**Mecanismo Proposto**:
- Vale deriva ~80-81% de receita de Iron Solutions (Q3 2025)
- ~60% dos contratos Vale precificados via índices (Platts IODEX) linked a SGX
- Gap temporal de ~1h entre fechamento SGX (12:00 UTC) e abertura B3 (13:00 UTC)
- Assimetria informacional: investidores asiáticos reagem primeiro a notícias de demanda chinesa

**Variáveis**:
| Variável | Descrição | Fonte |
|----------|-----------|-------|
| X (independente) | Retorno SGX Iron Ore 62% Fe | SGX/LSEG |
| Y (dependente) | Retorno VALE3 D+1 abertura ou D+1 fechamento | B3/MT5 |
| Controles | USD/BRL, VIX, volume SGX, dia da semana | Yahoo/LSEG |

### A.2 Janela Temporal de Análise

```
HORÁRIOS DE NEGOCIAÇÃO (UTC)

       00:00     06:00     12:00     18:00     24:00
         │         │         │         │         │
DCE      ├─────────┤                               01:00-07:00 UTC
         │ Day Session                             (22:00-04:00 BRT D-1)
         │
SGX T    ├─────────────────────┤                   23:25(D-1)-12:00 UTC
         │  T-Session                              (20:25-09:00 BRT)
         │
SGX T+1                        ├─────────────┤     12:00-20:45 UTC
                               │ T+1 Session       (09:00-17:45 BRT)
                               │
B3                             ├─────────────┤     13:00-20:55 UTC
                               │ Regular           (10:00-17:55 BRT)
         │         │         │
         ▼         ▼         ▼
    COLETA    SINAL      EXECUÇÃO
    DADOS    GERADO    10:05-10:30 BRT
```

**Janela crítica**: Fechamento SGX T-Session (09:00 BRT) → Abertura B3 (10:00 BRT) = 1 hora para processamento.

### A.3 Plano de Validação Estatística (Semana 2)

#### Fase 1: Estabelecer Racionalidade Econômica
- Por que minério deveria liderar VALE3?
- Testar hipótese contra alternativas (Vale lidera minério, sem relação)

#### Fase 2: Testes Estatísticos Sequenciais

| Teste | Propósito | Threshold de Sucesso |
|-------|-----------|---------------------|
| **Correlação Defasada** | Identificar lags significativos (1h, 4h, 1d) | r > 0.3 em pelo menos 2 lags |
| **Granger Causality** | Testar se minério "Granger-causa" VALE3 | p < 0.05 em 2+ janelas |
| **Cointegração Johansen** | Equilibrio de longo prazo | Vetor cointegrador significativo |
| **VAR com IRF** | Resposta de Vale a choques de minério | IRF positivo significativo |
| **Walk-Forward** | Robustez out-of-sample (60/20/20 split) | Sharpe > 1.0 após custos |

#### Fase 3: Robustez e Anti-Overfitting

| Método | Implementação |
|--------|---------------|
| Deflated Sharpe Ratio | Ajustar para múltiplos testes |
| Teste por Regime | Pré-COVID, COVID, pós-COVID |
| Bootstrap | 1000 resamples para CIs |
| Bonferroni/FDR | Correção para múltiplas comparações |

### A.4 Construção do Dataset

**Fontes de Dados**:

| Dado | Fonte Primária | Backup | Delay |
|------|----------------|--------|-------|
| Minério SGX 62% Fe | LSEG Workspace / Yahoo | Investing.com | 15-20min (delayed) |
| VALE3 | MT5 via Clear/XP | Cedro | Real-time |
| USD/BRL | Yahoo Finance | LSEG | 15min |
| VIX | Yahoo Finance | CBOE | 15min |
| Volume SGX | SGX data | LSEG | EOD |

**Tratamento Temporal Crítico**:
- Converter TODOS os timestamps para UTC
- Separar retornos overnight de retornos intraday
- Documentar feriados não-coincidentes (BR/SG/CN)
- Usar dados point-in-time para evitar look-ahead bias

### A.5 Critérios GO/NO-GO (Fim da Semana 2)

#### Critérios GO (todos devem ser atendidos):
```
✅ Granger significativo (p < 0.05) em pelo menos 2 janelas de lag
✅ Correlação defasada > 0.3 consistente em múltiplos subperíodos
✅ Walk-forward backtest com Sharpe > 1.0 após custos (0.25%)
✅ Max drawdown histórico < 15% no backtest
✅ Win rate > 50%
✅ Relação estável em pelo menos 2 regimes diferentes
```

#### Critérios NO-GO (qualquer um cancela projeto):
```
❌ Nenhuma significância estatística em qualquer lag
❌ Sharpe < 0.5 após custos
❌ Resultados instáveis (inversão de sinal entre subperíodos)
❌ Relação invertida (Vale lidera minério)
```

**Ação se NO-GO**: Documentar aprendizados detalhadamente; considerar hipóteses alternativas (outros pares: CSN, Usiminas); arquivar projeto se nenhuma alternativa viável.

---

## B. ESTRATÉGIAS DE TRADING (CONCEITUAIS)

### B.1 Estratégia 1: Sistema Baseado em Regras (Rule-Based)

**Conceito**: Gerar sinais quando variação do minério SGX excede limiar estatístico, com filtros de confirmação.

**Componentes de Decisão**:

| Elemento | Regra | Justificativa |
|----------|-------|---------------|
| **Entrada LONG** | Retorno minério > +1.5σ (vol 20d) | Movimento significativo |
| **Entrada SHORT** | Retorno minério < -1.5σ (vol 20d) | Movimento significativo inverso |
| **Confirmação 1** | Direção consistente últimas 2h SGX | Evitar ruído |
| **Confirmação 2** | USD/BRL variação < 0.5% | Isolar efeito câmbio |
| **Stop Loss** | 2x ATR(14) do preço de entrada | Baseado em volatilidade |
| **Take Profit** | 1:2 risco:retorno | R/R favorável |
| **Time Stop** | 5 dias úteis | Evitar posições estagnadas |

**Critérios de NO-TRADE**:
- VIX > 25 (mercado em estresse)
- Feriado em qualquer mercado (BR/SG/CN)
- Gap abertura B3 > 2% (evento overnight não antecipado)
- Correlação rolling 20d < 0.2 (relação quebrada)
- Dentro de 2h de anúncio macro agendado (FOMC, dados China)

**Perfil**: Baixa complexidade, alta transparência, rápida implementação.

### B.2 Estratégia 2: Modelo Preditivo (Machine Learning)

**Conceito**: Treinar modelo supervisionado para prever direção de VALE3 baseado em features de minério e variáveis auxiliares.

**Comparativo de Modelos**:

| Modelo | Prós | Contras | Recomendação |
|--------|------|---------|--------------|
| **Random Forest** | Robusto a overfitting; importância de features | Não captura dependências temporais | Baseline inicial |
| **XGBoost** | Alta performance; regularização L1/L2 | Requer tuning cuidadoso | Principal após RF |
| **LightGBM** | Mais rápido que XGBoost; bom para datasets grandes | Similar a XGBoost | Alternativa |
| **LSTM/GRU** | Captura padrões sequenciais | Propenso a overfitting; caixa-preta | Não recomendado MVP |

**Features Candidatas** (para feature selection):

| Categoria | Features | Janelas |
|-----------|----------|---------|
| **Minério** | Retorno, Z-score, volume relativo | 1h, 4h, sessão, D-1 |
| **Volatilidade** | ATR minério, σ VALE3, VIX | 5d, 10d, 20d |
| **Câmbio** | Retorno USD/BRL, volatilidade | 1d, 5d |
| **Spread** | SGX vs DCE | Sessão |
| **Calendário** | Dia semana, proximidade vencimento | Categórico |

**Validação Crítica**:
- Walk-forward com retreino mensal
- Holdout set separado (últimos 3 meses)
- Ablation study: remover features individualmente
- Deflated Sharpe Ratio para ajustar múltiplos testes

**Perfil**: Média complexidade, potencialmente maior alpha, requer mais dados.

### B.3 Estratégia 3: Híbrida Quant + Texto/Sentimento

**Conceito**: Combinar sinais quantitativos com análise de texto para modular posição ou vetar trades.

**Arquitetura em Duas Camadas**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   ESTRATÉGIA HÍBRIDA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CAMADA 1: SINAL QUANTITATIVO                                  │
│   ┌─────────────────────────────────────────┐                   │
│   │  Estratégia 1 (Regras) OU Estratégia 2  │                   │
│   │  → Gera sinal: LONG / SHORT / NEUTRO    │                   │
│   └─────────────────┬───────────────────────┘                   │
│                     │                                            │
│                     ▼                                            │
│   CAMADA 2: MODULAÇÃO POR TEXTO                                 │
│   ┌─────────────────────────────────────────┐                   │
│   │  Sentimento (FinBERT) + Event Detection │                   │
│   │  → Ajusta tamanho OU veta trade         │                   │
│   └─────────────────┬───────────────────────┘                   │
│                     │                                            │
│                     ▼                                            │
│   DECISÃO FINAL: Executar com sizing ajustado                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fontes de Texto Monitoradas**:
- Notícias de produção de aço chinês (Xinhua, Caixin, MySteel)
- Comunicados operacionais da Vale
- Notícias regulatórias/políticas brasileiras
- Eventos climáticos afetando portos

**Ações por Evento**:

| Tipo Evento | Ação | Exemplo |
|-------------|------|---------|
| Sentimento muito negativo | Veta trade LONG | Spike negativo em notícias |
| Evento raro detectado | Full stop | "Barragem", "greve", "acidente" |
| Sentimento positivo extremo | Aumenta sizing | Notícia de demanda chinesa |

**Perfil**: Alta complexidade, requer fase 2-3, maior custo operacional.

**Recomendação MVP**: Implementar Estratégia 1 nas semanas 1-4. Estratégias 2 e 3 são evolução futura.

---

## C. ARQUITETURA DO SISTEMA EM TEMPO REAL

### C.1 Diagrama de Arquitetura Completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA SISTEMA TRADING VALE3/MINÉRIO                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │                      CAMADA DE INGESTÃO                          │      │
│   ├──────────────────────────────────────────────────────────────────┤      │
│   │                                                                   │      │
│   │   ┌────────────┐   ┌────────────┐   ┌────────────┐              │      │
│   │   │  MINÉRIO   │   │   VALE3    │   │  AUXILIAR  │              │      │
│   │   │            │   │            │   │            │              │      │
│   │   │ Yahoo Fin  │   │ MT5 API    │   │ USD/BRL    │              │      │
│   │   │ LSEG (opt) │   │ Real-time  │   │ VIX        │              │      │
│   │   │ Investing  │   │ Histórico  │   │ Calendário │              │      │
│   │   └─────┬──────┘   └─────┬──────┘   └─────┬──────┘              │      │
│   │         │                │                │                      │      │
│   │         └────────────────┼────────────────┘                      │      │
│   │                          ▼                                       │      │
│   │                ┌─────────────────────┐                           │      │
│   │                │   DATA NORMALIZER   │                           │      │
│   │                │   (UTC alignment)   │                           │      │
│   │                │   (Staleness check) │                           │      │
│   │                └──────────┬──────────┘                           │      │
│   │                           │                                      │      │
│   └───────────────────────────┼──────────────────────────────────────┘      │
│                               │                                              │
│   ┌───────────────────────────┼──────────────────────────────────────┐      │
│   │                           ▼                                      │      │
│   │                ┌─────────────────────┐                           │      │
│   │                │    PostgreSQL       │                           │      │
│   │                │    + TimescaleDB    │                           │      │
│   │                │                     │                           │      │
│   │                │  • prices_iron_ore  │                           │      │
│   │                │  • prices_vale3     │                           │      │
│   │                │  • signals          │                           │      │
│   │                │  • orders           │                           │      │
│   │                │  • positions        │                           │      │
│   │                └──────────┬──────────┘                           │      │
│   │                           │                                      │      │
│   │           CAMADA DE DADOS │                                      │      │
│   └───────────────────────────┼──────────────────────────────────────┘      │
│                               │                                              │
│   ┌───────────────────────────┼──────────────────────────────────────┐      │
│   │                           ▼                                      │      │
│   │   ┌─────────────────────────────────────────────────────────┐    │      │
│   │   │                    FEATURE ENGINE                        │    │      │
│   │   ├─────────────────────────────────────────────────────────┤    │      │
│   │   │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │      │
│   │   │  │  Retornos  │  │ Volatility │  │ Correlation│        │    │      │
│   │   │  │  Minério   │  │  ATR / σ   │  │  Rolling   │        │    │      │
│   │   │  └────────────┘  └────────────┘  └────────────┘        │    │      │
│   │   │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │      │
│   │   │  │  Z-Score   │  │  USD/BRL   │  │    VIX     │        │    │      │
│   │   │  │  Momentum  │  │  Features  │  │   Regime   │        │    │      │
│   │   │  └────────────┘  └────────────┘  └────────────┘        │    │      │
│   │   └──────────────────────────┬──────────────────────────────┘    │      │
│   │                              │                                   │      │
│   │           CAMADA DE PROCESSAMENTO                                │      │
│   └──────────────────────────────┼───────────────────────────────────┘      │
│                                  │                                          │
│   ┌──────────────────────────────┼───────────────────────────────────┐      │
│   │                              ▼                                   │      │
│   │   ┌─────────────────────────────────────────────────────────┐    │      │
│   │   │                  SIGNAL GENERATOR                        │    │      │
│   │   ├─────────────────────────────────────────────────────────┤    │      │
│   │   │                                                          │    │      │
│   │   │   ┌────────────────────────────────────────────────┐    │    │      │
│   │   │   │              RULE-BASED ENGINE                  │    │    │      │
│   │   │   │                                                 │    │    │      │
│   │   │   │  IF retorno_minerio > 1.5σ AND filtros OK:     │    │    │      │
│   │   │   │     → SIGNAL = LONG, confiança = X%            │    │    │      │
│   │   │   │  ELIF retorno_minerio < -1.5σ AND filtros OK:  │    │    │      │
│   │   │   │     → SIGNAL = SHORT, confiança = X%           │    │    │      │
│   │   │   │  ELSE:                                          │    │    │      │
│   │   │   │     → SIGNAL = NEUTRAL                          │    │    │      │
│   │   │   │                                                 │    │    │      │
│   │   │   └─────────────────────────┬───────────────────────┘    │    │      │
│   │   │                             │                            │    │      │
│   │   └─────────────────────────────┼────────────────────────────┘    │      │
│   │                                 │                                 │      │
│   │           CAMADA DE ESTRATÉGIA  │                                 │      │
│   └─────────────────────────────────┼─────────────────────────────────┘      │
│                                     │                                        │
│   ┌─────────────────────────────────┼─────────────────────────────────┐      │
│   │                                 ▼                                 │      │
│   │   ┌─────────────────────────────────────────────────────────┐    │      │
│   │   │                    RISK ENGINE                           │    │      │
│   │   ├─────────────────────────────────────────────────────────┤    │      │
│   │   │                                                          │    │      │
│   │   │   ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │      │
│   │   │   │  Position  │  │    Stop    │  │    Loss    │        │    │      │
│   │   │   │   Sizing   │  │   Manager  │  │   Limits   │        │    │      │
│   │   │   │ (ATR-based)│  │ (Trailing) │  │ (Cascading)│        │    │      │
│   │   │   └────────────┘  └────────────┘  └────────────┘        │    │      │
│   │   │                                                          │    │      │
│   │   │   ┌──────────────────────────────────────────────┐      │    │      │
│   │   │   │              KILL SWITCH HIERARCHY           │      │    │      │
│   │   │   │   L1: Auto │ L2: Confirm │ L3: Manual │ L4  │      │    │      │
│   │   │   └──────────────────────────────────────────────┘      │    │      │
│   │   │                             │                            │    │      │
│   │   └─────────────────────────────┼────────────────────────────┘    │      │
│   │                                 │                                 │      │
│   │           CAMADA DE RISCO       │                                 │      │
│   └─────────────────────────────────┼─────────────────────────────────┘      │
│                                     │                                        │
│   ┌─────────────────────────────────┼─────────────────────────────────┐      │
│   │                                 ▼                                 │      │
│   │   ┌─────────────────────────────────────────────────────────┐    │      │
│   │   │                  EXECUTION ENGINE                        │    │      │
│   │   ├─────────────────────────────────────────────────────────┤    │      │
│   │   │                                                          │    │      │
│   │   │   ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │      │
│   │   │   │   Order    │  │    MT5     │  │   Fill     │        │    │      │
│   │   │   │  Generator │  │   Router   │  │  Tracker   │        │    │      │
│   │   │   │            │──▶│  (Broker) │──▶│            │        │    │      │
│   │   │   └────────────┘  └────────────┘  └────────────┘        │    │      │
│   │   │                                                          │    │      │
│   │   └─────────────────────────────────────────────────────────┘    │      │
│   │                                                                   │      │
│   │           CAMADA DE EXECUÇÃO                                     │      │
│   └───────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐      │
│   │                    CAMADA DE OBSERVABILIDADE                      │      │
│   ├──────────────────────────────────────────────────────────────────┤      │
│   │                                                                   │      │
│   │   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐│      │
│   │   │   Logs     │  │  Alertas   │  │ Dashboard  │  │   Audit    ││      │
│   │   │  Loguru    │  │  Telegram  │  │ Streamlit  │  │   Trail    ││      │
│   │   └────────────┘  └────────────┘  └────────────┘  └────────────┘│      │
│   │                                                                   │      │
│   └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### C.2 Comparação de Opções Tecnológicas

| Componente | Opção A (MVP) ✓ | Opção B (Semi-Pro) | Opção C (Institucional) |
|------------|-----------------|--------------------|-----------------------|
| **Linguagem** | Python 3.11+ | Python 3.11+ | Python + Java |
| **Dados minério** | Yahoo Finance (delayed) | LSEG Workspace | SGX direto + Platts |
| **Dados VALE3** | MT5 via Clear | Cedro WebSocket | Cedro + MT5 redundante |
| **Database** | **Supabase** (PostgreSQL gerenciado) | TimescaleDB VPS | TimescaleDB cluster |
| **Backend/Scheduler** | **Railway** (Python 24/7) | VPS dedicado | Cloud São Paulo |
| **Repositório** | **GitHub** | GitHub | GitHub Enterprise |
| **Fila mensagens** | Não necessário | Redis Streams | RabbitMQ |
| **Execução** | MT5 Python API (PC local) | MT5 + Cedro OMS | IB + Cedro + MT5 |
| **Custo mensal** | **R$25-50** | R$500-1.000 | R$3.000-5.000 |
| **Timeline MVP** | 4 semanas | 6-8 semanas | 8-12 semanas |

**Stack Escolhida (Opção A)**:
- **Supabase**: PostgreSQL gerenciado, grátis (Free tier: 500MB, 2GB transfer)
- **Railway**: Backend Python 24/7, ~R$25-50/mês
- **GitHub**: Repositório e CI/CD, grátis
- **Clear**: Corretora com MT5, corretagem zero
- **PC Local**: MT5 para execução de ordens (Windows)
- **Telegram**: Alertas, grátis

**Recomendação para R$20-50k**: **Opção A** para validar hipótese. Migrar para Opção B após 3 meses de operação lucrativa.

### C.3 Requisitos de Latência (Não é HFT)

| Componente | Latência Aceitável | Crítico se Exceder | Ação se Crítico |
|------------|-------------------|--------------------|-----------------|
| Dados minério | < 5 minutos | 15 minutos | Alert + pause |
| Cálculo features | < 30 segundos | 2 minutos | Alert |
| Geração sinal | < 10 segundos | 1 minuto | Alert |
| Submissão ordem | < 5 segundos | 30 segundos | Retry + alert |
| Confirmação fill | < 10 segundos | 1 minuto | Alert |

**Fallback obrigatório**: Se latência de dados > 15 min → sistema em modo seguro → cancela ordens pendentes → não abre novas posições.

### C.4 Stack Tecnológica Final (MVP)

```yaml
# requirements.txt

# Core
python>=3.11
pandas>=2.0
numpy>=1.24

# Database (Supabase)
supabase>=2.0
psycopg2-binary>=2.9

# Broker (Clear MT5)
MetaTrader5>=5.0.45

# Data Collection
yfinance>=0.2.28
requests>=2.31
beautifulsoup4>=4.12

# Analysis
statsmodels>=0.14
scipy>=1.11

# Operations
APScheduler>=3.10
python-telegram-bot>=20.0
loguru>=0.7
python-dotenv>=1.0

# Dashboard
streamlit>=1.30

# Testing
pytest>=7.4
```

**Arquitetura de Deploy**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA SIMPLIFICADA                      │
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
│   │  PC LOCAL    │───────────┘                                  │
│   │  (Windows)   │                                              │
│   │              │                                              │
│   │ • MT5 Clear  │  ◀── Necessário para execução de ordens     │
│   │ • Ordens     │                                              │
│   └──────────────┘                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Nota**: Docker não é necessário. Supabase fornece PostgreSQL gerenciado.

---

## D. USO DE LLM / NLP

### D.1 Avaliação Crítica: Onde NLP Agrega Valor

**Evidência de mercado**: Mesa de trading de banco de investimento NYC reportou >70% dos sinais NLP eram falsos positivos, e ~1/3 dos sinais corretos eram pequenos demais vs spread para serem tradáveis.

| Aplicação | Valor Real | Evidência |
|-----------|------------|-----------|
| Detecção de eventos raros | ALTO | Disrupções, acidentes, regulatório |
| Sumarização para revisão humana | ALTO | Economia de tempo do analista |
| Sentimento como fator adicional | MÉDIO | Estudos mostram 5-15% melhoria Sharpe (com risco de overfitting) |
| Sinais diretos de trading | BAIXO | Latência, falsos positivos, custo |

### D.2 Três Abordagens Recomendadas

#### Abordagem 1: Serviço de Sumarização (BAIXO RISCO) — Recomendado MVP

**Implementação**:
- FinBERT para scoring de sentimento (não LLM generativo)
- Sumarização diária usando LLM (GPT-4o-mini, Claude Haiku)
- Alertas para keywords críticas ("barragem", "greve", "acidente")

**Uso no Sistema**:
```
Sinal Quant + Sentimento Negativo Extremo → VETO no trade
Sinal Quant + Sentimento Neutro/Positivo → Executa normalmente
```

**Custo**: R$50-200/mês (API calls limitados)

#### Abordagem 2: Fator de Sentimento (MÉDIO RISCO) — Fase 2

**Implementação**:
- Score de sentimento como feature adicional no modelo ML
- Ablation study rigoroso para validar valor incremental
- Peso do fator ajustado por performance

**Validação Obrigatória**:
- Modelo COM sentimento vs modelo SEM sentimento
- Ganho no Sharpe > 0.2 para justificar complexidade
- Estabilidade do ganho em múltiplos períodos

**Custo**: R$200-500/mês

#### Abordagem 3: Event-Driven Trading (ALTO RISCO) — Não para MVP

**Por que evitar no MVP**:
- Latência de processamento LLM: 100ms-10s (muito lento)
- Problema de alucinação: LLMs erram ~6-54% em dados financeiros
- Custo escala rapidamente: GPT-4o = ~$3-15 por milhão de tokens
- Requer infraestrutura dedicada

### D.3 Mitigação de Alucinação e Viés

| Problema | Mitigação |
|----------|-----------|
| **Alucinação de fatos** | Usar RAG com fontes verificadas; FinBERT > LLM generativo |
| **Viés de sentimento** | Calibrar contra baseline manual; monitorar drift |
| **Falsos positivos** | Threshold alto para veto (sentimento < -0.8) |
| **Latência** | Pre-processar texto em background; não usar para sinais time-sensitive |

### D.4 Método de Avaliação (Ablation Study)

```
1. Período de teste: 6 meses de dados
2. Dividir em 3 subperíodos de 2 meses
3. Para cada subperíodo:
   - Modelo A: Sem texto
   - Modelo B: Com texto
4. Comparar Sharpe, Max DD, Win Rate
5. Aceitar texto SE:
   - Sharpe B > Sharpe A + 0.2 em todos subperíodos
   - Max DD B <= Max DD A
   - Diferença estatisticamente significativa (p < 0.05)
```

---

## E. GESTÃO DE RISCO E EXECUÇÃO

### E.1 Position Sizing

**Método Primário: ATR-Based com Risco Fixo**

```
Risco por trade = 1.5-2% do capital

Para conta de R$50.000:
- Risco máximo por trade: R$750-1.000
- ATR VALE3 (14 períodos) ≈ R$1,50 (estimativa)
- Stop = 2x ATR = R$3,00
- Tamanho posição = R$1.000 / R$3,00 = 333 ações
- Valor posição = 333 × R$60 = R$20.000 (40% da conta)
```

**Método Secundário: Fractional Kelly (Guia)**

```
Kelly = W - (1-W)/R

Onde:
- W = Win rate histórico (ex: 0.55)
- R = Ratio win/loss médio (ex: 2.0)

Kelly = 0.55 - (0.45)/2.0 = 0.55 - 0.225 = 0.325 (32.5%)

Usar: Quarter Kelly (8%) a Half Kelly (16%) como TETO
```

**Limites Absolutos (Independentes de Kelly)**:

| Limite | Valor | Justificativa |
|--------|-------|---------------|
| Posição única máxima | ≤ 20% do capital | Evitar concentração |
| Exposição direcional total | ≤ 50% do capital | Preservar caixa |
| Posições simultâneas | Máximo 3 | Gestão de atenção |

### E.2 Regras de Stop, Take-Profit e Time Stop

| Tipo | Parâmetro | Implementação |
|------|-----------|---------------|
| **Stop inicial** | 2x ATR(14) | Calculado na entrada; NUNCA mover contra posição |
| **Stop breakeven** | Ao atingir 1x risco | Mover stop para preço de entrada |
| **Trailing stop** | Chandelier Exit 1.5x ATR | Após atingir 2x risco |
| **Take-profit parcial** | 50% em 1x risco | Reduz exposição, garante lucro parcial |
| **Take-profit final** | 2x risco | R:R 1:2 |
| **Time stop** | 5 dias úteis | Se posição não progrediu 50% do target |

### E.3 Limites de Perda em Cascata

| Período | Limite | Ação ao Atingir |
|---------|--------|-----------------|
| **Diário** | 2.5% (R$1.250 em R$50k) | HALT automático; zero trades resto do dia |
| **Semanal** | 5% (R$2.500) | Reduzir tamanho 50% na semana seguinte |
| **Mensal** | 10% (R$5.000) | Cessar trading 5 dias úteis; revisar estratégia |
| **Drawdown máximo** | 20% (R$10.000) | FULL STOP; revalidação completa da hipótese |

### E.4 Custos e Fricções (Estimativas para VALE3)

| Componente | Estimativa | Notas |
|------------|-----------|-------|
| Taxas B3 (emolumentos) | ~0.030% por lado | ~0.06% round-trip |
| Corretagem (Clear/XP) | 0-0.05% | Zero em muitos casos |
| Spread bid-ask VALE3 | 0.03-0.05% | Mega-cap muito líquida |
| Slippage (ordem < R$50k) | 0.05-0.10% | Impacto negligenciável |
| **Total round-trip** | **0.15-0.25%** | Orçar 0.25% conservadoramente |

**Implicação**: Estratégia precisa gerar > 0.25% por trade para empatar. Para holding 1-5 dias, isto é hurdle significativo.

### E.5 Kill Switches (Hierarquia)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        HIERARQUIA DE KILL SWITCHES                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║   [NÍVEL 1: AUTOMÁTICO - IMEDIATO]                                        ║
║   ├── Loss limit diário atingido (2.5%)                                   ║
║   │   └── AÇÃO: HALT todas operações, alerta Telegram                     ║
║   ├── Dados stale > 60 segundos                                           ║
║   │   └── AÇÃO: ALERT + cancelar ordens pendentes                         ║
║   ├── Dados stale > 5 minutos                                             ║
║   │   └── AÇÃO: FECHAR posições a mercado                                 ║
║   └── 3 ordens rejeitadas em 10 minutos                                   ║
║       └── AÇÃO: PAUSE + investigar API                                    ║
║                                                                            ║
║   [NÍVEL 2: AUTOMÁTICO COM CONFIRMAÇÃO]                                   ║
║   ├── Divergência preço > 2% entre fontes                                 ║
║   │   └── AÇÃO: ALERT + pause para revisão manual                         ║
║   ├── 3 trades perdedores consecutivos                                    ║
║   │   └── AÇÃO: PAUSE 30 minutos                                          ║
║   └── Correlação rolling < 0.2 por 5 dias                                 ║
║       └── AÇÃO: FLAG para revisão manual da hipótese                      ║
║                                                                            ║
║   [NÍVEL 3: MANUAL OBRIGATÓRIO]                                           ║
║   ├── Posição > 10% da conta                                              ║
║   │   └── AÇÃO: Requer aprovação manual                                   ║
║   ├── Override de qualquer safety limit                                   ║
║   │   └── AÇÃO: Requer justificativa documentada                          ║
║   └── Primeiro trade em instrumento novo                                  ║
║       └── AÇÃO: Requer teste prévio                                       ║
║                                                                            ║
║   [NÍVEL 4: BOTÃO DE PÂNICO]                                              ║
║   ├── Software kill switch (comando /kill no Telegram)                    ║
║   │   └── AÇÃO: Cancelar tudo + fechar posições                           ║
║   ├── Contato emergencial corretora                                       ║
║   │   └── AÇÃO: Número 24h documentado e acessível                        ║
║   └── Desligar máquina/VPS                                                ║
║       └── AÇÃO: Último recurso                                            ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## F. MONITORAMENTO, GOVERNANÇA E OPERACIONAL

### F.1 Métricas de Performance e Risco

**Métricas de Performance (calcular diariamente)**:
- P&L realizado e não-realizado
- Win rate rolling 20 trades
- Profit factor (gross profit / gross loss)
- Average win vs average loss
- Sharpe ratio rolling 30/60/90 dias
- Sortino ratio (downside risk)

**Métricas de Risco (monitorar real-time)**:
- Exposição atual (% da conta)
- Distância ao stop (em R$ e %)
- Drawdown atual vs máximo histórico
- Correlação rolling VALE3 vs minério (20 dias)
- VIX / volatilidade implícita

**Métricas Operacionais (auditar semanalmente)**:
- Slippage médio vs esperado
- Latência média do pipeline
- Taxa de rejeição de ordens
- Uptime do sistema
- Discrepâncias de reconciliação

### F.2 Observabilidade: Logs, Alertas, Auditoria

**Logging Obrigatório por Ordem**:
```json
{
  "timestamp_ms": 1704067200000,
  "order_id_internal": "ORD-2024-001",
  "order_id_exchange": "12345678",
  "symbol": "VALE3",
  "side": "BUY",
  "quantity": 333,
  "price": 60.00,
  "type": "LIMIT",
  "signal_reason": "SGX_RETORNO_+2.1%_>_1.5STD",
  "signal_confidence": 0.75,
  "status": "FILLED",
  "fill_price": 60.02,
  "slippage_bps": 3.3
}
```

**Retenção**: 5 anos (requisito regulatório)

**Alertas Configurados**:

| Evento | Canal | Urgência |
|--------|-------|----------|
| Ordem executada | Log | Baixa |
| Loss limit 50% atingido | Email | Média |
| Loss limit 100% atingido | Telegram | Alta |
| Dados stale | Telegram | Alta |
| API error | Email + Log | Média |
| Drawdown > 15% | Telegram + SMS | Crítica |
| Correlação < 0.2 por 3 dias | Email | Média |

### F.3 Checklist Operacional Diário

**Pré-Mercado (antes das 09:30 BRT)**:
- [ ] Verificar status de conexões (MT5, data feeds)
- [ ] Revisar posições abertas overnight
- [ ] Checar calendário (feriados em BR/SG/CN?)
- [ ] Verificar notícias relevantes overnight (Vale, minério, China)
- [ ] Confirmar capital disponível vs margens
- [ ] Verificar sinal gerado pela sessão asiática

**Durante Mercado (10:00-17:55)**:
- [ ] Monitorar dashboard de métricas (a cada 30 min)
- [ ] Verificar execução de ordens
- [ ] Responder a alertas imediatamente
- [ ] Registrar observações no log

**Pós-Mercado (após 18:00 BRT)**:
- [ ] Reconciliar posições (sistema vs extrato corretora)
- [ ] Documentar trades do dia com justificativas
- [ ] Calcular métricas diárias
- [ ] Backup de logs e database
- [ ] Revisar erros ou anomalias
- [ ] Atualizar planilha de tracking

### F.4 Critérios Objetivos para Pausar Sistema

| Trigger | Ação | Duração Pausa |
|---------|------|---------------|
| Drawdown > 15% | Revisão parcial | 3 dias úteis |
| Drawdown > 20% | Full stop + revalidação | Indefinido até aprovação |
| Win rate < 40% em 30 trades | Análise de drift | 5 dias úteis |
| Correlação minério-VALE3 < 0.2 por 10 dias | Hipótese questionada | Revalidação estatística |
| 3 meses sem retorno positivo | Sunset da estratégia | Descontinuação |
| Evento Vale tipo Brumadinho | Full stop imediato | Avaliação caso-a-caso |
| Sharpe rolling 90d < 0.5 | Reduzir capital 50% | Investigação |

---

## G. PLANO DE IMPLEMENTAÇÃO EM 4 SEMANAS

### G.1 Visão Geral

```
SEMANA 1          SEMANA 2          SEMANA 3          SEMANA 4
───────────────────────────────────────────────────────────────────►

┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│  INFRA  │      │ VALIDA- │      │ EXECUÇÃO│      │  TESTES │
│    +    │  ──► │   ÇÃO   │  ──► │    +    │  ──► │    +    │
│  DADOS  │      │  STAT   │      │  RISCO  │      │ GO-LIVE │
└─────────┘      └─────────┘      └─────────┘      └─────────┘
     │                │                │                │
     ▼                ▼                ▼                ▼
• Pipeline         • Granger         • MT5 integrado  • Paper trading
• Database         • Backtest        • Stops impl.    • Dashboard
• Coleta auto      • GO/NO-GO        • Kill switches  • Go-live 10%

                      │
                      ▼
              ╔═══════════════╗
              ║   GATE 1:     ║
              ║ GO ou NO-GO?  ║
              ╚═══════════════╝
```

### G.2 Semana 1: Infraestrutura e Dados

#### Dias 1-2: Setup Inicial

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Criar repositório Git privado | Repo no GitHub | Estrutura de diretórios conforme arquitetura |
| Setup ambiente Python | pyproject.toml ou requirements.txt | Poetry/pip install sem erros |
| Criar projeto Supabase | Projeto ativo em supabase.com | Dashboard acessível, credenciais no .env |
| Criar tabelas no Supabase | Schemas via SQL Editor | prices_iron_ore, prices_vale3, signals, orders |
| Verificar conta Clear | Acesso ao app/site | Login funcionando |
| Solicitar MT5 (se necessário) | Credenciais MT5 | Pode levar 1-3 dias úteis |
| Instalar MetaTrader 5 | MT5 conectado | Login na conta Clear-Demo |

#### Dias 3-4: Pipeline de Dados Minério

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar iron_ore_fetcher.py | Código funcional | Yahoo Finance retornando dados |
| Backup scraper Investing.com | Código funcional | Fallback operacional |
| Persistência no Supabase | Função save_iron_ore_price() | Dados persistindo na tabela |
| Scheduler coleta 5 minutos | APScheduler config | Coleta automática funcionando |

#### Dias 5-7: Pipeline VALE3 e Auxiliares

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar vale_fetcher.py via MT5 | Código funcional | Dados real-time de VALE3 |
| Persistir VALE3 no Supabase | Função save_vale_price() | Dados na tabela prices_vale3 |
| Implementar auxiliary_fetcher.py | USD/BRL, VIX coletando | Dados no Supabase |
| Script de backfill histórico | 6-12 meses de dados | Dataset completo para análise |
| Notebook análise exploratória | Visualizações básicas | Correlação descritiva calculada |

**Checkpoint Semana 1**:
- [ ] Supabase com tabelas criadas e dados fluindo
- [ ] Coleta minério 24h sem falhas
- [ ] Coleta VALE3 pregão completo sem falhas
- [ ] MT5 conectando e retornando dados via Clear
- [ ] 6+ meses de histórico disponível
- [ ] Notebook exploratório mostrando correlações iniciais

### G.3 Semana 2: Validação Estatística (CRÍTICA)

#### Dias 8-9: Features e Preparação

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar features.py | Retornos, volatilidade, z-score | Cálculos corretos |
| Alinhamento temporal UTC | Dataset unificado | Timestamps consistentes |
| Criar dataset para análise | CSV/Parquet consolidado | Pronto para testes |

#### Dias 10-11: Testes Estatísticos

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Teste de correlação com lags | Notebook com resultados | Correlações por lag documentadas |
| Teste de Granger Causality | Notebook com p-values | Significância em múltiplos lags |
| Teste de Cointegração Johansen | Resultados documentados | Vetor cointegrador se aplicável |
| Análise por subperíodo | Estabilidade avaliada | Resultados em 3+ períodos |

#### Dias 12-14: Backtest e Decisão GO/NO-GO

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar signal_generator.py | Estratégia 1 (regras) | Sinais gerando corretamente |
| Backtest walk-forward | Sharpe, win rate, DD | Métricas após custos (0.25%) |
| Sensitivity analysis | Parâmetros testados | Robustez a variações |
| Documento de decisão GO/NO-GO | Relatório formal | Critérios avaliados |

**GATE 1 — Decisão GO/NO-GO**:

| Critério | Threshold | Status |
|----------|-----------|--------|
| Granger p-value | < 0.05 em 2+ lags | [ ] Atendido / [ ] Não atendido |
| Correlação defasada | > 0.3 | [ ] Atendido / [ ] Não atendido |
| Sharpe walk-forward | > 1.0 após custos | [ ] Atendido / [ ] Não atendido |
| Win rate | > 50% | [ ] Atendido / [ ] Não atendido |
| Max drawdown backtest | < 15% | [ ] Atendido / [ ] Não atendido |
| Estabilidade por regime | Consistente em 2+ períodos | [ ] Atendido / [ ] Não atendido |

**Se NO-GO**: Documentar aprendizados. Considerar:
1. Outros pares (CSN, Usiminas)
2. Outras janelas temporais
3. Arquivar projeto se nenhuma alternativa viável

### G.4 Semana 3: Execução e Risco (se GO)

#### Dias 15-16: Integração MT5

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar mt5_connector.py | Conexão autenticada | Login sem erros |
| Funções de envio de ordens | MARKET, LIMIT, STOP | Ordens em conta demo |
| Funções de consulta de posições | Posições e histórico | Dados corretos |
| Tratamento de erros e retries | Lógica de fallback | Resiliência a falhas |

#### Dias 17-18: Gestão de Risco

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar position_sizing.py | ATR-based sizing | Cálculos corretos |
| Implementar risk_limits.py | Daily/weekly/monthly limits | Limites enforced |
| Implementar kill_switch.py | Níveis 1-4 | Triggers testados |

#### Dias 19-21: Stops e Orquestração

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Lógica de stops (inicial, breakeven, trailing) | Stop manager | Stops funcionando em demo |
| Implementar main_loop.py | Loop de execução | Pipeline end-to-end |
| Alertas Telegram | Bot configurado | Mensagens chegando |
| Testes integrados | Testes E2E em demo | 3 dias sem erros |

### G.5 Semana 4: Testes Finais e Go-Live Gradual

#### Dias 22-24: Deploy Railway + Paper Trading

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Criar projeto no Railway | Projeto configurado | Dashboard Railway acessível |
| Configurar variáveis de ambiente | Todas as vars do .env | SUPABASE_URL, TELEGRAM_TOKEN, etc. |
| Deploy do scheduler/bot | Serviço rodando 24/7 | Logs mostrando coleta de dados |
| Paper trading 3 dias | Trades simulados | Zero erros técnicos |
| Documentar desvios e bugs | docs/paper_trading_issues.md | Bugs corrigidos |

**Nota**: MT5 continua rodando no PC local. Railway apenas para coleta de dados e geração de sinais. Execução de ordens requer MT5 no PC.

#### Dias 25-26: Dashboard e Documentação

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Implementar dashboard (Streamlit) | Dashboard funcional | Métricas visíveis |
| Manual de operações | Documento | Procedimentos documentados |
| Troubleshooting guide | Documento | Erros comuns e soluções |
| Checklists diários | Templates | Prontos para uso |

#### Dias 27-28: Go-Live Gradual

| Tarefa | Entregável | Critério de Aceite |
|--------|------------|-------------------|
| Review final de segurança | Checklist completo | Todos itens verificados |
| Verificar capital na Clear | R$2-5k disponível | Saldo visível no MT5 |
| Mudar para conta REAL no MT5 | Conexão Clear-Real | mt5.account_info() mostra conta real |
| Primeiro trade real (se sinal) | Trade executado | Ordem no extrato da Clear |
| Monitoramento intensivo D+1 | Relatório pós-trade | Performance conforme esperado |

**Critérios para Escalar Capital**:
- 2 semanas de operação sem erros técnicos
- Performance dentro de ±20% do backtest
- Nenhum trigger de pause ativado
- Reconciliação perfeita (posições = extrato corretora)

**Ramp-Up de Capital**:
| Semana | Capital (%) | Capital (R$) | Condição |
|--------|-------------|--------------|----------|
| 4 | 10% | R$2-5k | Go-live inicial |
| 6 | 25% | R$5-12.5k | 2 semanas sem erros |
| 8 | 50% | R$10-25k | Performance OK |
| 10+ | 100% | R$20-50k | Confiança estabelecida |

### G.6 Riscos do Cronograma

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Validação estatística negativa | MÉDIA | Projeto cancelado | Gate claro; documentar e pivotar |
| Atraso aprovação MT5 na Clear | BAIXA | 1-3 dias delay | Iniciar solicitação Dia 1 |
| Dados minério inacessíveis | BAIXA | Requer alternativas | Yahoo Finance + Investing.com backup |
| Bugs em integração MT5 | MÉDIA | Paper trading estendido | Testes extensivos em conta demo |
| Supabase free tier insuficiente | MUITO BAIXA | Upgrade necessário | Free tier suficiente para MVP (500MB) |
| Railway downtime | BAIXA | Coleta interrompida | Health checks + restart automático |
| PC local offline | MÉDIA | Ordens não executam | Alertas Telegram + checklist diário |

**Custos Mensais Estimados**:
| Serviço | Custo |
|---------|-------|
| Supabase | Grátis (Free tier) |
| Railway | ~R$25-50/mês |
| Clear | Grátis (corretagem zero) |
| Telegram | Grátis |
| **Total** | **~R$25-50/mês** |

---

## H. POR QUE ESTA ESTRATÉGIA PODE FALHAR: 18 CENÁRIOS CRÍTICOS

### Categoria 1: Decaimento de Alpha e Ciclo de Vida

**1. Crowding de Sinal e Competição**
- **Risco**: Relações lead-lag são arbitradas quando mais traders descobrem a mesma ineficiência
- **Evidência**: Custos de decay de alpha: 9.9% anualmente na Europa, 5.6% nos EUA (Maven Securities)
- **Detecção**: Sharpe ratio declinante; lucro médio por trade reduzindo; slippage aumentando
- **Mitigação**: Monitorar decay via métricas rolling; aceitar vida útil finita (12-24 meses)

**2. Desaparecimento da Relação Lead-Lag**
- **Risco**: Relação estatística deixa de existir ou se inverte
- **Evidência**: Brooks et al. (2001) demonstra que mesmo efeitos identificáveis são frequentemente não-lucrativos após custos
- **Detecção**: Correlação defasada não significativa; lag ótimo instável
- **Mitigação**: Usar métodos de lag dinâmico; análise de breakeven estrita

**3. Novos Participantes Eliminando Ineficiência**
- **Risco**: HFT e algoritmos sofisticados capturam alpha antes
- **Evidência**: HFT representa 28%+ do volume de futuros (vs 22% em 2009)
- **Detecção**: Volume eletrônico aumentando; resposta de preço a notícias mais rápida
- **Mitigação**: Aceitar vida útil finita; não competir em latência

### Categoria 2: Quebra de Correlação e Mudança de Regime

**4. Mudança de Regime de Correlação Commodity-Equity**
- **Risco**: Correlações stock-commodity mudam drasticamente em crises
- **Evidência**: BIS mostra variação de -0.39 a 0.76 entre 1962-2012
- **Detecção**: VIX spiking; spreads de crédito alargando
- **Mitigação**: Algoritmos de detecção de regime; reduzir posição em regimes de alta correlação

**5. Desacoplamento Minério de Ferro × Vale**
- **Risco**: Vale diverge de minério por fatores específicos (câmbio, custos, ESG)
- **Detecção**: Beta da Vale ao minério mudando; divergência em cobertura de analistas
- **Mitigação**: Monitorar correlação rolling; threshold de pausa (< 0.2)

**6. Mudança de Regime de Demanda Chinesa**
- **Risco**: China responde por ~70% da demanda de minério; mudança estrutural invalidaria padrões
- **Detecção**: Ratio sucata-para-aço aumentando; starts imobiliários caindo; estoques portuários
- **Mitigação**: Monitorar fundamentos do setor de aço chinês; considerar sunset se mudança estrutural

### Categoria 3: Eventos Específicos da Vale e Cisnes Negros

**7. Desastre de Barragem / Evento ESG**
- **Risco**: Brumadinho (Jan 2019) causou queda de 24% em um dia, $19 bilhões perdidos
- **Detecção**: Mínima — desastres são imprevisíveis
- **Mitigação**: Limites de posição estritos; stops (com risco de gap); hedges de tail-risk (puts)

**8. Volatilidade BRL/USD Dominando Sinal**
- **Risco**: Vale fatura em USD mas reporta em BRL; USD/BRL é extremamente volátil
- **Detecção**: Volatilidade implícita BRL spiking; crise política brasileira
- **Mitigação**: Adicionar filtro de volatilidade BRL; considerar spread ADR vs B3

**9. Risco Político/Regulatório Brasileiro**
- **Risco**: Proibições operacionais, suspensão de dividendos, multas ambientais
- **Detecção**: Ciclos eleitorais; ações de enforcement ambiental
- **Mitigação**: Monitorar news feeds brasileiros; reduzir exposição em incerteza política

### Categoria 4: Falhas Técnicas e Operacionais

**10. Falhas de Feed de Dados / Preços Stale**
- **Risco**: Futuros de minério em múltiplas exchanges; liquidez pode cair drasticamente
- **Detecção**: Gaps de preço entre fontes; timestamps atrasando; spreads anormais
- **Mitigação**: Múltiplos feeds redundantes; detecção de staleness automática

**11. Slippage de Execução Durante Baixa Liquidez**
- **Risco**: Executar em janelas de baixa liquidez causa slippage substancial
- **Detecção**: Spreads bid-ask alargando; profundidade do order book reduzindo
- **Mitigação**: Limitar trading a janelas de alta liquidez; usar limit orders

**12. Downtime de API/Infraestrutura em Momentos Críticos**
- **Risco**: Flash crashes coincidem com sobrecarga de sistemas
- **Detecção**: Latência aumentando; taxa de erro de APIs subindo
- **Mitigação**: Conectividade redundante; kill switch; orders limite pré-posicionadas

### Categoria 5: Armadilhas Estatísticas e de Backtesting

**13. Overfitting de Backtest**
- **Risco**: Com 5 anos de dados, não mais que 45 variações deveriam ser testadas (López de Prado)
- **Evidência**: Quantopian: R² < 0.025 entre Sharpe in-sample e out-of-sample
- **Detecção**: Sharpe > 3.0 no backtest; sensibilidade a pequenas mudanças de parâmetros
- **Mitigação**: Registrar todos testes; usar Deflated Sharpe Ratio; limitar graus de liberdade

**14. Viés de Sobrevivência em Backtest**
- **Risco**: Testar apenas Vale ignora outras empresas que falharam
- **Detecção**: Testar apenas Vale vs minério sem outros pares
- **Mitigação**: Usar databases livres de survivorship bias; testar lógica em múltiplos ativos

**15. Subestimação de Custos de Transação**
- **Risco**: Backtest com 15% anual pode colapsar para zero após custos reais
- **Detecção**: Turnover maior que esperado; custos reais > premissas
- **Mitigação**: Modelar custos 2x esperado; incluir slippage baseado em fills históricos

### Categoria 6: Estrutura de Mercado e Fatores Externos

**16. Mudanças de Regras de Exchange**
- **Risco**: SGX, DCE, B3 podem mudar margens, horários ou limites com aviso limitado
- **Detecção**: Consultas regulatórias; revisões de metodologia
- **Mitigação**: Monitorar anúncios; manter margem excess

**17. Mudança Macro de Regime (Cisne Negro)**
- **Risco**: COVID-19, guerras comerciais, eventos geopolíticos causam spikes de correlação imprevisíveis
- **Detecção**: Escalação geopolítica; ações de política sem precedentes
- **Mitigação**: Manter posições pequenas; critérios explícitos de shutdown

**18. Projeto Simandou Alterando Dinâmica de Supply**
- **Risco**: Nova capacidade de 120Mt da Guiné (2026-2027) pode alterar fundamentalmente o mercado
- **Detecção**: Anúncios de progresso do projeto; mudanças na participação de mercado
- **Mitigação**: Monitorar publicações da indústria; considerar sunset se estrutura mudar

---

## CONCLUSÃO E SÍNTESE

### Síntese do Projeto

Este documento consolida três análises anteriores (pesquisa_quant.md, roadmap_mvp_trading_mineiro_vale3.md, roadmap-minerals-quant-fund.md) em um plano de execução único para um sistema de trading quantitativo explorando a relação temporal entre futuros de minério de ferro e VALE3.

### Descoberta Mais Importante

**A hipótese central carece de validação acadêmica publicada.** Nenhum estudo peer-reviewed foi encontrado examinando especificamente esta relação lead-lag. Isto significa que a implementação é **exploratória, não confirmatória**.

### Decisões-Chave

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| Stack | Python + MT5 + PostgreSQL | Rapidez de desenvolvimento, custo baixo |
| Estratégia inicial | Rule-based (Estratégia 1) | Transparente, sem overfitting, rápida |
| Position sizing | ATR-based, 1.5-2% risco | Conservador para capital pequeno |
| LLM/NLP | Apenas para alertas/sumarização | Evitar alucinação e latência |
| Timeline | 4 semanas até go-live 10% | Agressivo mas realista |
| Gate crítico | Semana 2 (GO/NO-GO) | Validação antes de investir em código |

### Recomendações Finais Prioritizadas

1. **Validação estatística rigorosa (Semana 2)** — Ponto de decisão GO/NO-GO antes de qualquer capital em risco

2. **Começar com infraestrutura mínima (Opção A)** — ~R$200-500/mês para preservar capital para trading

3. **Escalar capital gradualmente** — 10% → 25% → 50% → 100% condicionado a performance

4. **Definir critérios de sunset antecipadamente** — 3 meses sem retorno positivo, DD > 20%, ou correlação < 0.2 por 10 dias

5. **Documentar tudo** — Registrar todas análises, trades e decisões para aprendizado

### Honestidade Epistêmica

A maioria das estratégias quantitativas **não funcionam** após implementação real. O valor deste exercício está tanto em validar uma oportunidade quanto em descobrir, com rigor metodológico, que ela não existe — evitando assim a perda de capital em uma tese inválida.

---

## APÊNDICE: CHECKLISTS

### Checklist Técnico Pré-Go-Live

```
INFRAESTRUTURA:
□ Supabase com dados fluindo 48h+
□ Railway rodando scheduler 24/7
□ MT5 conectado à conta Clear-Real
□ Telegram bot respondendo comandos

TÉCNICO:
□ Todos os testes unitários passando
□ Paper trading 3+ dias sem erros críticos
□ Kill switches testados (incluindo /kill Telegram)
□ Alertas funcionando
□ Dashboard mostrando métricas
□ Logs sendo gravados no Railway
□ Documentação completa
```

### Checklist de Risco Pré-Go-Live

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

### Checklist Operacional Pré-Go-Live

```
□ Capital na conta Clear (R$2-5k inicial)
□ MT5 logado na conta Clear-Real
□ PC local ligado e conectado
□ Railway rodando sem erros
□ Supabase acessível
□ Celular com Telegram configurado
□ Manual de operações lido
□ Contato Clear emergência anotado: 4020-1500
□ Checklist diário acessível
```

---

## COMPARATIVO: DOCUMENTOS CONSOLIDADOS

| Aspecto | pesquisa_quant.md | roadmap_mvp.md | roadmap-minerals.md | **Este Documento** |
|---------|-------------------|----------------|--------------------|--------------------|
| **Foco** | Pesquisa conceitual | Implementação técnica | Institucional | **Consolidado** |
| **Timeline** | 4 semanas | 4 semanas | 10 semanas | **4 semanas** |
| **Capital** | R$20-50k | R$20-50k | R$20-50k teste | **R$20-50k** |
| **Stack** | Opções comparadas | Decisões finais | Stack profissional | **MVP com upgrade path** |
| **Validação** | Muito detalhada | Básica | Detalhada | **Completa com gates** |
| **Modos de falha** | 18 cenários | 10 riscos | 7 riscos | **18 completos** |
| **LLM/NLP** | Crítica detalhada | Não abordado | Planejado | **Abordagem conservadora** |
| **Arquitetura** | Diagrama básico | Detalhada | Muito detalhada | **Camadas completas** |
| **Kill switches** | Hierarquia 4 níveis | Implementação | Conceitual | **Hierarquia implementável** |

---

**Documento consolidado por**: Claude (Anthropic)
**Fontes consolidadas**:
- pesquisa_quant.md
- roadmap_mvp_trading_mineiro_vale3.md
- roadmap-minerals-quant-fund.md
- Pesquisas Perplexity (Janeiro 2026)

**Versão**: 3.0 (Stack Simplificada: Supabase + Railway + Clear)
**Data**: Janeiro 2026

**Stack Final**:
| Componente | Serviço | Custo Mensal |
|------------|---------|--------------|
| Database | Supabase | Grátis |
| Backend | Railway | R$25-50 |
| Repositório | GitHub | Grátis |
| Corretora | Clear (MT5) | Grátis |
| Alertas | Telegram | Grátis |
| **Total** | | **R$25-50/mês** |
