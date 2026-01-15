# TRACK.md — Acompanhamento de Tarefas por Semana

> Sistema de Trading Quantitativo VALE3/Minério de Ferro
> **Atualizado em**: Janeiro 2026
> **Stack**: Supabase + Railway + GitHub + Clear (MT5)

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| `[ ]` | Tarefa pendente |
| `[~]` | Em progresso |
| `[x]` | Concluída |
| `[!]` | Bloqueada |
| `||` | Pode ser feita em paralelo com outras marcadas `||` |
| `->` | Depende da tarefa anterior |
| `GATE` | Ponto de decisão crítico |

---

## Infraestrutura Escolhida

| Componente | Serviço | Custo |
|------------|---------|-------|
| Database | **Supabase** (PostgreSQL gerenciado) | Grátis (tier free) |
| Backend/Bot | **Railway** (Python 24/7) | ~$5-10/mês |
| Repositório | **GitHub** | Grátis |
| Corretora | **Clear** (MT5) | Grátis |
| MT5 Runtime | **PC local** (Windows) | Grátis |
| Alertas | **Telegram** | Grátis |

**Custo mensal estimado**: ~R$25-50/mês (apenas Railway)

---

## SEMANA 1: Infraestrutura e Dados

### Dias 1-2: Setup Inicial

#### Trilha A: Repositório e Ambiente `||`
```
[ ] A1.1 Criar repositório privado no GitHub
    Entregável: Repo com estrutura de diretórios
    Critério: git clone funcional
    Tempo: 30min

[ ] A1.2 Setup ambiente Python local com Poetry/pip
    Entregável: pyproject.toml ou requirements.txt
    Critério: poetry install / pip install sem erros
    Tempo: 1h

[ ] A1.3 Configurar pre-commit hooks (black, ruff, mypy)
    Entregável: .pre-commit-config.yaml
    Critério: pre-commit run --all-files passa
    Depende de: A1.2
    Tempo: 30min

[ ] A1.4 Criar .env.example e .gitignore
    Entregável: Arquivos de configuração
    Critério: Credenciais não expostas
    Tempo: 15min
```

#### Trilha B: Supabase (Substitui Docker + PostgreSQL local) `||`
```
[ ] B1.1 Criar projeto no Supabase
    Entregável: Projeto ativo em supabase.com
    Critério: Dashboard acessível
    Tempo: 10min

[ ] B1.2 Obter credenciais de conexão
    Entregável: URL, anon key, service key no .env
    Critério: Conexão via psycopg2 funciona
    Tempo: 15min

[ ] B1.3 Criar tabelas via SQL Editor ou migrations
    Entregável: Tabelas prices_iron_ore, prices_vale3, signals, orders
    Critério: Schemas criados corretamente
    Tempo: 1h

    SQL de referência:
    - prices_iron_ore (timestamp, source, price, volume)
    - prices_vale3 (timestamp, open, high, low, close, volume)
    - auxiliary_data (timestamp, usd_brl, vix)
    - signals (timestamp, direction, confidence, features_json)
    - orders (timestamp, order_id, symbol, side, qty, price, status)

[ ] B1.4 Testar conexão Python → Supabase
    Entregável: Script test_supabase.py
    Critério: INSERT e SELECT funcionando
    Depende de: B1.2, B1.3
    Tempo: 30min
```

#### Trilha C: Conta Clear + MT5 (INICIAR DIA 1) `||`
```
[ ] C1.1 Verificar conta Clear ativa
    Entregável: Login funcionando no app/site
    Critério: Acesso à conta confirmado
    Tempo: 15min

[ ] C1.2 Solicitar acesso ao MT5 (se não tiver)
    Entregável: Credenciais MT5 recebidas
    Critério: Login e senha do MT5
    NOTA: Pode levar 1-3 dias úteis
    Tempo: 15min + espera

[ ] C1.3 Instalar MetaTrader 5 no PC
    Entregável: MT5 instalado e conectado
    Critério: Login na conta Clear-Demo ou Clear-Real
    Tempo: 30min

[ ] C1.4 Instalar biblioteca MetaTrader5 Python
    Entregável: pip install MetaTrader5
    Critério: import MetaTrader5 funciona
    Depende de: A1.2
    Tempo: 10min

[ ] C1.5 Testar conexão Python → MT5
    Entregável: Script test_mt5.py
    Critério: mt5.initialize() retorna True, dados de VALE3 retornando
    Depende de: C1.3, C1.4
    Tempo: 30min
```

### Dias 3-4: Pipeline de Dados — Minério

#### Trilha D: Conectores de Minério `||`
```
[ ] D1.1 Implementar src/data/iron_ore_fetcher.py (Yahoo Finance)
    Entregável: Classe IronOreFetcher
    Critério: Retorna preços SGX 62% Fe (ticker: pode ser necessário pesquisar)
    Tempo: 2h

[ ] D1.2 Implementar backup scraper (Investing.com)
    Entregável: Classe InvestingFetcher
    Critério: Fallback funcional com BeautifulSoup
    Depende de: D1.1
    Tempo: 2h

[ ] D1.3 Implementar persistência no Supabase
    Entregável: Função save_iron_ore_price()
    Critério: Dados persistindo na tabela prices_iron_ore
    Depende de: B1.4, D1.1
    Tempo: 1h
```

#### Trilha E: Scheduler Local (depois Railway) `||`
```
[ ] E1.1 Configurar APScheduler para coleta automática
    Entregável: src/scheduler/jobs.py
    Critério: Coleta a cada 5 minutos rodando local
    Depende de: D1.3
    Tempo: 1h

[ ] E1.2 Implementar health check e logging
    Entregável: Logs estruturados com loguru
    Critério: Falhas são logadas com contexto
    Depende de: E1.1
    Tempo: 1h
```

### Dias 5-7: Pipeline VALE3 e Auxiliares

#### Trilha F: Dados VALE3 via MT5 `||`
```
[ ] F1.1 Implementar src/data/vale_fetcher.py
    Entregável: Classe ValeFetcher usando MT5
    Critério: Dados real-time de VALE3
    Depende de: C1.5
    Tempo: 2h

[ ] F1.2 Persistir dados VALE3 no Supabase
    Entregável: Função save_vale_price()
    Critério: Dados na tabela prices_vale3
    Depende de: B1.4, F1.1
    Tempo: 1h

[ ] F1.3 Coletar dados históricos VALE3 (6-12 meses)
    Entregável: Histórico no banco
    Critério: Dados desde Jan/Jul 2025
    Depende de: F1.2
    Tempo: 1h
```

#### Trilha G: Dados Auxiliares `||`
```
[ ] G1.1 Implementar src/data/auxiliary_fetcher.py
    Entregável: Classe para USD/BRL e VIX (Yahoo Finance)
    Critério: Dados coletando corretamente
    Tempo: 1h

[ ] G1.2 Persistir dados auxiliares no Supabase
    Entregável: Tabela auxiliary_data populada
    Critério: USD/BRL e VIX no banco
    Depende de: B1.4, G1.1
    Tempo: 30min
```

#### Trilha H: Backfill e Análise Inicial (Sequencial)
```
[ ] H1.1 Script de backfill histórico minério (6-12 meses)
    Entregável: src/data/backfill.py
    Critério: Dataset completo para análise
    Depende de: D1.3, F1.3, G1.2
    Tempo: 2h

[ ] H1.2 Notebook de análise exploratória inicial
    Entregável: notebooks/01_exploratory.ipynb
    Critério: Visualizações de correlação, estatísticas descritivas
    Depende de: H1.1
    Tempo: 3h
```

### Checkpoint Semana 1
```
GATE: Verificar antes de prosseguir para Semana 2

[ ] Supabase com tabelas criadas e dados fluindo
[ ] Pipeline minério 24h sem falhas
[ ] Pipeline VALE3 pregão completo sem falhas
[ ] MT5 conectando e retornando dados
[ ] 6+ meses de histórico disponível
[ ] Notebook exploratório mostrando correlações iniciais
```

---

## SEMANA 2: Validação Estatística (CRÍTICA)

### Dias 8-9: Features e Preparação

#### Trilha I: Feature Engineering `||`
```
[ ] I2.1 Implementar src/features/returns.py
    Entregável: Cálculo de retornos em múltiplas janelas
    Critério: Retornos 1h, 4h, sessão, D-1
    Tempo: 2h

[ ] I2.2 Implementar src/features/volatility.py
    Entregável: ATR, desvio padrão rolling
    Critério: Cálculos corretos em 5d, 10d, 20d
    Tempo: 2h

[ ] I2.3 Implementar src/features/zscore.py
    Entregável: Z-score de retornos
    Critério: Normalização correta
    Tempo: 1h
```

#### Trilha J: Dataset Unificado (Sequencial)
```
[ ] J2.1 Alinhamento temporal UTC
    Entregável: src/features/alignment.py
    Critério: Timestamps consistentes minério + VALE3
    Depende de: I2.1, I2.2, I2.3
    Tempo: 2h

[ ] J2.2 Criar dataset consolidado para análise
    Entregável: Tabela analysis_dataset no Supabase ou Parquet local
    Critério: Pronto para testes estatísticos
    Depende de: J2.1
    Tempo: 1h
```

### Dias 10-11: Testes Estatísticos

#### Trilha K: Análises Paralelas `||`
```
[ ] K2.1 Notebook: Correlação com lags
    Entregável: notebooks/02_correlation_lags.ipynb
    Critério: Correlações por lag documentadas (1h, 4h, sessão)
    Depende de: J2.2
    Tempo: 2h

[ ] K2.2 Notebook: Teste de Granger Causality
    Entregável: notebooks/03_granger_causality.ipynb
    Critério: p-values para múltiplos lags
    Depende de: J2.2
    Tempo: 2h

[ ] K2.3 Notebook: Cointegração Johansen
    Entregável: notebooks/04_cointegration.ipynb
    Critério: Vetor cointegrador se aplicável
    Depende de: J2.2
    Tempo: 2h

[ ] K2.4 Notebook: Análise por subperíodo
    Entregável: notebooks/05_subperiod_stability.ipynb
    Critério: Resultados em 3+ períodos (pré-COVID, COVID, pós)
    Depende de: J2.2
    Tempo: 2h
```

### Dias 12-14: Backtest e Decisão GO/NO-GO

#### Trilha L: Backtest (Sequencial)
```
[ ] L2.1 Implementar src/strategy/signal_generator.py
    Entregável: Estratégia 1 (rule-based)
    Critério: Sinais LONG/SHORT/NEUTRAL
    Depende de: K2.1
    Tempo: 3h

[ ] L2.2 Implementar src/backtest/engine.py
    Entregável: Motor de backtest walk-forward
    Critério: Métricas calculadas corretamente
    Depende de: L2.1
    Tempo: 4h

[ ] L2.3 Backtest walk-forward (60/20/20)
    Entregável: notebooks/06_backtest_walkforward.ipynb
    Critério: Sharpe, win rate, max DD após custos (0.25%)
    Depende de: L2.2
    Tempo: 3h

[ ] L2.4 Sensitivity analysis
    Entregável: notebooks/07_sensitivity.ipynb
    Critério: Robustez a variações de parâmetros
    Depende de: L2.3
    Tempo: 2h
```

#### Trilha M: Documentação de Decisão (Sequencial)
```
[ ] M2.1 Compilar relatório de decisão GO/NO-GO
    Entregável: docs/decision_gate_week2.md
    Critério: Todos os critérios avaliados objetivamente
    Depende de: K2.1, K2.2, K2.3, K2.4, L2.3, L2.4
    Tempo: 2h
```

### GATE 1: Decisão GO/NO-GO (Fim da Semana 2)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                           GATE GO/NO-GO                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  CRITÉRIOS GO (TODOS devem ser atendidos):                            ║
║                                                                        ║
║  [ ] Granger p-value < 0.05 em 2+ lags                                ║
║  [ ] Correlação defasada > 0.3 em múltiplos subperíodos               ║
║  [ ] Sharpe walk-forward > 1.0 após custos (0.25%)                    ║
║  [ ] Win rate > 50%                                                   ║
║  [ ] Max drawdown backtest < 15%                                      ║
║  [ ] Estabilidade em 2+ regimes diferentes                            ║
║                                                                        ║
║  CRITÉRIOS NO-GO (QUALQUER UM cancela):                               ║
║                                                                        ║
║  [ ] Nenhuma significância estatística                                ║
║  [ ] Sharpe < 0.5 após custos                                         ║
║  [ ] Inversão de sinal entre subperíodos                              ║
║  [ ] Relação invertida (Vale lidera minério)                          ║
║                                                                        ║
║  DECISÃO: [ ] GO — Prosseguir para Semana 3                           ║
║           [ ] NO-GO — Documentar e encerrar/pivotar                   ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## SEMANA 3: Execução e Risco (SE GO)

### Dias 15-16: Integração MT5 para Execução

#### Trilha N: Conexão MT5 Execução `||`
```
[ ] N3.1 Implementar src/execution/mt5_connector.py
    Entregável: Classe MT5Connector completa
    Critério: Login, envio de ordens, consulta de posições
    Tempo: 4h

[ ] N3.2 Funções de envio de ordens (MARKET, LIMIT, STOP)
    Entregável: send_order(), modify_order(), cancel_order()
    Critério: Ordens executando em conta DEMO
    Depende de: N3.1
    Tempo: 3h

[ ] N3.3 Funções de consulta de posições e histórico
    Entregável: get_positions(), get_history(), get_balance()
    Critério: Dados corretos e reconciliados
    Depende de: N3.1
    Tempo: 2h
```

#### Trilha O: Resiliência `||`
```
[ ] O3.1 Decorator retry com backoff exponencial
    Entregável: src/utils/retry.py
    Critério: Resiliência a falhas temporárias de conexão
    Tempo: 1h

[ ] O3.2 Reconexão automática MT5
    Entregável: Lógica de reconexão no connector
    Critério: Recupera de desconexões sem intervenção
    Depende de: O3.1, N3.1
    Tempo: 1h
```

### Dias 17-18: Gestão de Risco

#### Trilha P: Position Sizing `||`
```
[ ] P3.1 Implementar src/risk/position_sizing.py
    Entregável: Classe PositionSizer (ATR-based)
    Critério: Cálculos corretos para capital configurado
    Tempo: 2h

[ ] P3.2 Implementar limites absolutos
    Entregável: Validação max 20% por posição, max 50% total
    Critério: Ordens rejeitadas se exceder limites
    Depende de: P3.1
    Tempo: 1h
```

#### Trilha Q: Limites de Perda `||`
```
[ ] Q3.1 Implementar src/risk/loss_limits.py
    Entregável: Classe LossLimits
    Critério: Daily (2.5%), Weekly (5%), Monthly (10%)
    Tempo: 2h

[ ] Q3.2 Implementar cascata de ações automáticas
    Entregável: HALT, reduzir sizing, full stop
    Critério: Ações executam automaticamente ao atingir limite
    Depende de: Q3.1
    Tempo: 1h
```

#### Trilha R: Kill Switches `||`
```
[ ] R3.1 Implementar src/risk/kill_switch.py
    Entregável: Classe KillSwitch (4 níveis)
    Critério: Todos triggers implementados
    Tempo: 2h

[ ] R3.2 Criar bot Telegram para alertas e comandos
    Entregável: src/alerts/telegram_bot.py
    Critério: /status, /kill, /pause funcionando
    Tempo: 2h

[ ] R3.3 Integrar kill switch com Telegram
    Entregável: Comando /kill fecha todas posições
    Critério: Full stop via Telegram testado
    Depende de: R3.1, R3.2
    Tempo: 1h
```

### Dias 19-21: Stops e Orquestração

#### Trilha S: Stop Manager (Sequencial)
```
[ ] S3.1 Implementar src/risk/stop_manager.py
    Entregável: Stop inicial (2x ATR), breakeven, trailing
    Critério: Stops calculados corretamente
    Depende de: P3.1
    Tempo: 3h

[ ] S3.2 Testar stops em conta demo
    Entregável: Log de 10 trades simulados
    Critério: Stops executando nos níveis corretos
    Depende de: S3.1, N3.2
    Tempo: 2h
```

#### Trilha T: Loop Principal (Sequencial)
```
[ ] T3.1 Implementar src/main_loop.py
    Entregável: Loop de execução completo
    Critério: Coleta → Features → Sinal → Risco → Execução
    Depende de: TODAS as trilhas N, O, P, Q, R, S
    Tempo: 4h

[ ] T3.2 Alertas Telegram para eventos
    Entregável: Alertas de ordem, stop, erro
    Critério: Mensagens chegando no celular
    Depende de: T3.1, R3.2
    Tempo: 1h

[ ] T3.3 Testes integrados E2E em demo
    Entregável: 3 dias de operação contínua em demo
    Critério: Zero erros críticos, stops funcionando
    Depende de: T3.2
    Tempo: 3 dias
```

### Checkpoint Semana 3
```
[ ] MT5 executando ordens em demo corretamente
[ ] Position sizing calculando e limitando
[ ] Loss limits enforced automaticamente
[ ] Kill switches testados (incluindo /kill Telegram)
[ ] Stop manager operacional
[ ] Loop principal rodando 3 dias sem erros
[ ] Alertas Telegram chegando
```

---

## SEMANA 4: Deploy, Testes Finais e Go-Live

### Dias 22-24: Deploy Railway + Paper Trading

#### Trilha U: Deploy no Railway `||`
```
[ ] U4.1 Criar projeto no Railway
    Entregável: Projeto configurado
    Critério: Dashboard Railway acessível
    Tempo: 15min

[ ] U4.2 Configurar variáveis de ambiente no Railway
    Entregável: Todas as vars do .env configuradas
    Critério: SUPABASE_URL, TELEGRAM_TOKEN, etc.
    Tempo: 30min

[ ] U4.3 Deploy do scheduler/bot
    Entregável: Serviço rodando 24/7
    Critério: Logs mostrando coleta de dados
    Depende de: U4.2
    Tempo: 1h

[ ] U4.4 Configurar health checks e restart automático
    Entregável: Railway reinicia se serviço cair
    Critério: Uptime > 99%
    Depende de: U4.3
    Tempo: 30min

NOTA: MT5 continua rodando no PC local. Railway apenas
      para coleta de dados e geração de sinais.
      Execução de ordens requer MT5 no PC.
```

#### Trilha V: Paper Trading (Sequencial)
```
[ ] V4.1 Paper trading 3 dias completos
    Entregável: Log de trades simulados
    Critério: Zero erros técnicos
    Depende de: U4.3, T3.3
    Tempo: 3 dias

[ ] V4.2 Documentar todos desvios e bugs
    Entregável: docs/paper_trading_issues.md
    Critério: Todos bugs identificados e corrigidos
    Depende de: V4.1
    Tempo: 2h

[ ] V4.3 Validar métricas vs backtest
    Entregável: Comparativo em planilha/notebook
    Critério: Dentro de ±30% do esperado
    Depende de: V4.1
    Tempo: 1h
```

### Dias 25-26: Dashboard e Documentação

#### Trilha W: Dashboard Streamlit `||`
```
[ ] W4.1 Implementar dashboard básico
    Entregável: src/dashboard/app.py
    Critério: P&L, posições, últimos sinais
    Tempo: 3h

[ ] W4.2 Métricas de risco no dashboard
    Entregável: Drawdown atual, correlação rolling
    Critério: Atualizando com dados do Supabase
    Depende de: W4.1
    Tempo: 2h

[ ] W4.3 Deploy dashboard no Railway (opcional)
    Entregável: URL pública do dashboard
    Critério: Acessível de qualquer lugar
    Depende de: W4.2
    Tempo: 1h
```

#### Trilha X: Documentação `||`
```
[ ] X4.1 Manual de operações
    Entregável: docs/operations_manual.md
    Critério: Procedimentos diários documentados
    Tempo: 2h

[ ] X4.2 Troubleshooting guide
    Entregável: docs/troubleshooting.md
    Critério: Erros comuns e soluções
    Tempo: 1h

[ ] X4.3 Checklists diários
    Entregável: docs/daily_checklist.md
    Critério: Template pronto para uso
    Tempo: 30min
```

### Dias 27-28: Go-Live Gradual

#### Trilha Y: Go-Live (Sequencial)
```
[ ] Y4.1 Review final de segurança
    Entregável: Checklist completo assinado
    Critério: Todos itens verificados
    Depende de: V4.2, W4.2, X4.1
    Tempo: 2h

[ ] Y4.2 Verificar capital na Clear
    Entregável: R$2-5k disponível para trading
    Critério: Saldo visível no MT5
    Tempo: 15min (ou transferência 1-2 dias)

[ ] Y4.3 Mudar para conta REAL no MT5
    Entregável: Conexão com Clear-Real
    Critério: mt5.account_info() mostra conta real
    Depende de: Y4.2
    Tempo: 15min

[ ] Y4.4 Primeiro trade real (quando sinal aparecer)
    Entregável: Trade executado
    Critério: Ordem no extrato da Clear
    Depende de: Y4.3
    Tempo: Variável

[ ] Y4.5 Monitoramento intensivo D+1
    Entregável: Relatório pós-trade
    Critério: Performance conforme esperado
    Depende de: Y4.4
    Tempo: 1 dia
```

### Checklist Final Semana 4
```
╔═══════════════════════════════════════════════════════════════════════╗
║                         CHECKLIST PRÉ-GO-LIVE                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  INFRAESTRUTURA:                                                       ║
║  [ ] Supabase com dados fluindo 48h+                                  ║
║  [ ] Railway rodando scheduler 24/7                                   ║
║  [ ] MT5 conectado à conta Clear-Real                                 ║
║  [ ] Telegram bot respondendo comandos                                ║
║                                                                        ║
║  TÉCNICO:                                                              ║
║  [ ] Paper trading 3+ dias sem erros                                  ║
║  [ ] Kill switches testados                                           ║
║  [ ] Alertas funcionando                                              ║
║  [ ] Dashboard mostrando métricas                                     ║
║                                                                        ║
║  RISCO:                                                                ║
║  [ ] Position sizing validado                                         ║
║  [ ] Stop loss testado em demo                                        ║
║  [ ] Daily loss limit testado                                         ║
║  [ ] Comando /kill testado                                            ║
║                                                                        ║
║  OPERACIONAL:                                                          ║
║  [ ] Capital na conta Clear (R$2-5k)                                  ║
║  [ ] PC com MT5 ligado e conectado                                    ║
║  [ ] Celular com Telegram configurado                                 ║
║  [ ] Manual de operações lido                                         ║
║  [ ] Contato Clear emergência anotado                                 ║
║                                                                        ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## Resumo de Paralelização por Semana

### Semana 1
```
Dia 1-2:
┌─────────────────────────────────────────────────────────────┐
│  Trilha A (GitHub + Python)  ││  PARALELO                   │
│  Trilha B (Supabase)         ││  Dia 1-2                    │
│  Trilha C (Clear + MT5)      ││                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 3-4:
┌─────────────────────────────────────────────────────────────┐
│  Trilha D (Minério fetcher)  ││  PARALELO                   │
│  Trilha E (Scheduler)        ││  Dia 3-4                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 5-7:
┌─────────────────────────────────────────────────────────────┐
│  Trilha F (VALE3 fetcher)    ││  PARALELO                   │
│  Trilha G (Auxiliares)       ││  Dia 5-6                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Trilha H (Backfill + Análise) │  SEQUENCIAL - Dia 7        │
└─────────────────────────────────────────────────────────────┘
```

### Semana 2
```
Dia 8-9:
┌─────────────────────────────────────────────────────────────┐
│  I2.1, I2.2, I2.3 (Features)   │  PARALELO                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Trilha J (Dataset unificado)  │  SEQUENCIAL                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 10-11:
┌─────────────────────────────────────────────────────────────┐
│  K2.1, K2.2, K2.3, K2.4        │  PARALELO (4 notebooks)    │
│  (Correlação, Granger, Coint)  │                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 12-14:
┌─────────────────────────────────────────────────────────────┐
│  Trilha L (Backtest)           │  SEQUENCIAL                │
│  Trilha M (Decisão GO/NO-GO)   │                            │
└─────────────────────────────────────────────────────────────┘
```

### Semana 3
```
Dia 15-16:
┌─────────────────────────────────────────────────────────────┐
│  Trilha N (MT5 execução)     ││  PARALELO                   │
│  Trilha O (Resiliência)      ││                             │
└─────────────────────────────────────────────────────────────┘

Dia 17-18:
┌─────────────────────────────────────────────────────────────┐
│  Trilha P (Sizing)           ││  PARALELO                   │
│  Trilha Q (Loss Limits)      ││                             │
│  Trilha R (Kill Switch)      ││                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 19-21:
┌─────────────────────────────────────────────────────────────┐
│  Trilha S (Stop Manager)       │  SEQUENCIAL                │
│  Trilha T (Loop Principal)     │                            │
└─────────────────────────────────────────────────────────────┘
```

### Semana 4
```
Dia 22-24:
┌─────────────────────────────────────────────────────────────┐
│  Trilha U (Railway deploy)     │  SEQUENCIAL                │
│  Trilha V (Paper trading)      │  3 dias                    │
└─────────────────────────────────────────────────────────────┘

Dia 25-26:
┌─────────────────────────────────────────────────────────────┐
│  Trilha W (Dashboard)        ││  PARALELO                   │
│  Trilha X (Documentação)     ││                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Dia 27-28:
┌─────────────────────────────────────────────────────────────┐
│  Trilha Y (Go-Live)            │  SEQUENCIAL                │
└─────────────────────────────────────────────────────────────┘
```

---

## Estimativa de Esforço Atualizada

| Semana | Horas Estimadas | Foco Principal |
|--------|-----------------|----------------|
| 1 | 25-30h | Infra + Dados |
| 2 | 30-35h | Validação Estatística |
| 3 | 35-40h | Execução + Risco |
| 4 | 25-30h + 3 dias paper | Deploy + Go-Live |

**Total**: ~115-135 horas de trabalho + 3 dias de paper trading

---

## Custos Mensais (Após Go-Live)

| Serviço | Custo |
|---------|-------|
| Supabase | Grátis (Free tier) |
| Railway | ~R$25-50/mês |
| Clear | Grátis (corretagem zero) |
| Telegram | Grátis |
| **Total** | **~R$25-50/mês** |

---

## Histórico de Atualizações

| Data | Versão | Mudança |
|------|--------|---------|
| 2026-01-XX | 1.0 | Criação inicial |
| 2026-01-XX | 2.0 | Migração para Supabase + Railway + Clear |

---

*Documento atualizado para arquitetura simplificada com serviços gerenciados.*
