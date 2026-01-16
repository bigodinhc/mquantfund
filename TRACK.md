# TRACK.md — Acompanhamento de Tarefas por Semana

> Sistema de Trading Quantitativo VALE3/Minério de Ferro
> **Atualizado em**: Janeiro 2026
> **Stack**: Supabase + GitHub Actions + Clear (MT5)

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

## Documentação de Referência

| Documento | Descrição |
|-----------|-----------|
| `docs/GUIA_VALIDACAO_ESTATISTICA.md` | Guia completo sobre Walk-Forward, Granger, Thresholds, etc. |
| `roadmap-fundo-quant-vale3-4semanas.md` | Roadmap consolidado do projeto |
| `CLAUDE.md` | Contexto técnico para desenvolvimento |

---

## Infraestrutura Escolhida

| Componente | Serviço | Custo |
|------------|---------|-------|
| Database | **Supabase** (PostgreSQL gerenciado) | Grátis (tier free) |
| Scheduler/Jobs | **GitHub Actions** (cron jobs) | Grátis (2000 min/mês) |
| Repositório | **GitHub** | Grátis |
| Corretora | **Clear** (MT5) | Grátis |
| MT5 Runtime | **PC local** (Windows) | Grátis |
| Alertas | **Telegram** | Grátis |

**Custo mensal estimado**: R$0 (100% gratuito)

---

## SEMANA 1: Infraestrutura e Dados

### Dias 1-2: Setup Inicial

#### Trilha A: Repositório e Ambiente `||`
```
[x] A1.1 Criar repositório privado no GitHub
    Entregável: Repo com estrutura de diretórios
    Critério: git clone funcional
    Tempo: 30min
    NOTA: Repo quantfund criado e funcional

[x] A1.2 Setup ambiente Python local com Poetry/pip
    Entregável: pyproject.toml ou requirements.txt
    Critério: poetry install / pip install sem erros
    Tempo: 1h
    NOTA: .venv criado com requirements.txt

[ ] A1.3 Configurar pre-commit hooks (black, ruff, mypy)
    Entregável: .pre-commit-config.yaml
    Critério: pre-commit run --all-files passa
    Depende de: A1.2
    Tempo: 30min

[x] A1.4 Criar .env.example e .gitignore
    Entregável: Arquivos de configuração
    Critério: Credenciais não expostas
    Tempo: 15min
    NOTA: .env configurado com credenciais LSEG e Supabase
```

#### Trilha B: Supabase (Substitui Docker + PostgreSQL local) `||`
```
[x] B1.1 Criar projeto no Supabase
    Entregável: Projeto ativo em supabase.com
    Critério: Dashboard acessível
    Tempo: 10min
    NOTA: Projeto "quantfund" criado (ID: chhcuivssqrkimwocera)

[x] B1.2 Obter credenciais de conexão
    Entregável: URL, anon key, service key no .env
    Critério: Conexão via psycopg2 funciona
    Tempo: 15min
    NOTA: Credenciais em .env, conexão funcionando

[x] B1.3 Criar tabelas via SQL Editor ou migrations
    Entregável: Tabelas prices_iron_ore, prices_vale3, signals, orders
    Critério: Schemas criados corretamente
    Tempo: 1h
    NOTA: Migrações 001_initial_schema.sql, 002_pg_cron_setup.sql,
          003_add_futures_fields.sql aplicadas

    SQL de referência:
    - prices_iron_ore (timestamp, source, price, volume, variable_key, expiry_date)
    - prices_vale3 (timestamp, open, high, low, close, volume)
    - auxiliary_data (timestamp, usd_brl, vix)
    - signals (timestamp, direction, confidence, features_json)
    - orders (timestamp, order_id, symbol, side, qty, price, status)

[x] B1.4 Testar conexão Python → Supabase
    Entregável: Script test_supabase.py
    Critério: INSERT e SELECT funcionando
    Depende de: B1.2, B1.3
    Tempo: 30min
    NOTA: SupabaseClient em jobs/clients/supabase_client.py funcionando
```

#### Trilha C: Conta Clear + MT5 (INICIAR DIA 1) `||`
```
[x] C1.1 Verificar conta Clear ativa
    Entregável: Login funcionando no app/site
    Critério: Acesso à conta confirmado
    Tempo: 15min
    NOTA: Conta Clear ativa

[x] C1.2 Solicitar acesso ao MT5 (se não tiver)
    Entregável: Credenciais MT5 recebidas
    Critério: Login e senha do MT5
    NOTA: Pode levar 1-3 dias úteis
    Tempo: 15min + espera
    NOTA: Conta demo MT5 liberada

[x] C1.3 Instalar MetaTrader 5 no PC
    Entregável: MT5 instalado e conectado
    Critério: Login na conta Clear-Demo ou Clear-Real
    Tempo: 30min
    NOTA: MT5 instalado e logado

[x] C1.4 Instalar biblioteca MetaTrader5 Python
    Entregável: pip install MetaTrader5
    Critério: import MetaTrader5 funciona
    Depende de: A1.2
    Tempo: 10min
    NOTA: Biblioteca instalada no Python Windows

[x] C1.5 Testar conexão Python → MT5
    Entregável: Script test_mt5.py
    Critério: mt5.initialize() retorna True, dados de VALE3 retornando
    Depende de: C1.3, C1.4
    Tempo: 30min
    NOTA: Conexão Python → MT5 funcionando!
```

### Dias 3-4: Pipeline de Dados — Minério

#### Trilha D: Conectores de Minério `||`
```
[x] D1.1 Implementar src/data/iron_ore_fetcher.py (Yahoo Finance)
    Entregável: Classe IronOreFetcher
    Critério: Retorna preços SGX 62% Fe (ticker: pode ser necessário pesquisar)
    Tempo: 2h
    NOTA: Implementado em jobs/ingestion/fetch_iron_ore.py usando LSEG Workspace
          Coleta 12 contratos forward (SZZFF6 a SZZFZ6) com variable_key

[ ] D1.2 Implementar backup scraper (Investing.com)
    Entregável: Classe InvestingFetcher
    Critério: Fallback funcional com BeautifulSoup
    Depende de: D1.1
    Tempo: 2h
    NOTA: Pendente - LSEG é fonte primária suficiente por ora

[x] D1.3 Implementar persistência no Supabase
    Entregável: Função save_iron_ore_price()
    Critério: Dados persistindo na tabela prices_iron_ore
    Depende de: B1.4, D1.1
    Tempo: 1h
    NOTA: insert_iron_ore_prices() em supabase_client.py - 12 contratos inseridos
```

#### Trilha E: Scheduler Local (depois Railway) `||`
```
[~] E1.1 Configurar APScheduler para coleta automática
    Entregável: src/scheduler/jobs.py
    Critério: Coleta a cada 5 minutos rodando local
    Depende de: D1.3
    Tempo: 1h
    NOTA: jobs/scripts/collect_all.py criado (execução manual)
          APScheduler pendente - scripts bash disponíveis (cron_realtime.sh)

[x] E1.2 Implementar health check e logging
    Entregável: Logs estruturados com loguru
    Critério: Falhas são logadas com contexto
    Depende de: E1.1
    Tempo: 1h
    NOTA: Logging com loguru implementado em todos os fetchers
```

### Dias 5-7: Pipeline VALE3 e Auxiliares

#### Trilha F: Dados VALE3 via MT5 `||`
```
[x] F1.1 Implementar src/data/vale_fetcher.py
    Entregável: Classe ValeFetcher usando MT5
    Critério: Dados real-time de VALE3
    Depende de: C1.5
    Tempo: 2h
    NOTA: Implementado em jobs/ingestion/fetch_vale3.py usando LSEG (VALE3.SA)
          MT5 será usado para execução, não para coleta de dados

[x] F1.2 Persistir dados VALE3 no Supabase
    Entregável: Função save_vale_price()
    Critério: Dados na tabela prices_vale3
    Depende de: B1.4, F1.1
    Tempo: 1h
    NOTA: insert_vale3_prices() em supabase_client.py funcionando

[ ] F1.3 Coletar dados históricos VALE3 (6-12 meses)
    Entregável: Histórico no banco
    Critério: Dados desde Jan/Jul 2025
    Depende de: F1.2
    Tempo: 1h
    NOTA: Pendente - fetch_vale3.py suporta --mode historical
```

#### Trilha G: Dados Auxiliares `||`
```
[x] G1.1 Implementar src/data/auxiliary_fetcher.py
    Entregável: Classe para USD/BRL e VIX (Yahoo Finance)
    Critério: Dados coletando corretamente
    Tempo: 1h
    NOTA: Implementado em jobs/ingestion/fetch_auxiliary.py usando LSEG
          USD/BRL (BRL=) funcionando
          VIX (.VIX) NÃO disponível na assinatura LSEG - usar Yahoo como fallback

[x] G1.2 Persistir dados auxiliares no Supabase
    Entregável: Tabela auxiliary_data populada
    Critério: USD/BRL e VIX no banco
    Depende de: B1.4, G1.1
    Tempo: 30min
    NOTA: insert_auxiliary_data() em supabase_client.py funcionando
```

#### Trilha H: Backfill e Análise Inicial (Sequencial)
```
[x] H1.1 Script de backfill histórico minério (5 ANOS)
    Entregável: jobs/ingestion/backfill_historical.py
    Critério: Dataset completo para análise
    Depende de: D1.3, F1.3, G1.2
    Tempo: 2h
    NOTA: Backfill implementado com LSEG (SGX SZZFc2) + Yahoo Finance
          - Minério SGX: 1,300 registros (2021-01 a 2026-01)
          - VALE3: 1,758 registros (2021-01 a 2026-01)
          - USD/BRL: 1,305 registros
          - VIX: 1,305 registros
          Uso: python -m jobs.ingestion.backfill_historical --years 5

[x] H1.2 Notebook de análise exploratória inicial
    Entregável: notebooks/01_exploratory_analysis.ipynb
    Critério: Visualizações de correlação, estatísticas descritivas
    Depende de: H1.1
    Tempo: 3h
    NOTA: Notebook completo com:
          - Carregamento de dados do Supabase
          - Normalização (forward fill + filtro B3)
          - Correlação de preços e retornos
          - Teste de Granger
          - Análise lead-lag
          - Matriz de correlação
```

### Checkpoint Semana 1
```
GATE: Verificar antes de prosseguir para Semana 2

[x] Supabase com tabelas criadas e dados fluindo
[x] Pipeline minério 24h sem falhas (GitHub Actions daily-tasks.yml)
[x] Pipeline VALE3 pregão completo sem falhas (incluído no backfill)
[x] MT5 conectando e retornando dados (Python Windows → MT5 funcionando)
[x] 5 ANOS de histórico disponível (backfill_historical.py executado)
[x] Notebook exploratório mostrando correlações iniciais

✅ SEMANA 1 CONCLUÍDA - Pronto para Semana 2
```

---

## SEMANA 2: Validação Estatística (CRÍTICA)

> **REFERÊNCIA**: Consultar `docs/GUIA_VALIDACAO_ESTATISTICA.md` para explicação detalhada de cada conceito.

### Dias 8-9: Features e Preparação

#### Trilha I: Feature Engineering `||`
```
[x] I2.1 Implementar src/features/returns.py
    Entregável: Cálculo de retornos em múltiplas janelas
    Critério: Retornos 1d, 5d, 10d, 20d + momentum + cumulativo
    Tempo: 2h
    NOTA: Implementado com calculate_returns(), add_return_features(),
          calculate_momentum(), calculate_lagged_returns()

[x] I2.2 Implementar src/features/volatility.py
    Entregável: ATR, desvio padrão rolling
    Critério: Cálculos corretos em 5d, 10d, 20d + ATR 14d/20d
    Tempo: 2h
    NOTA: Implementado com calculate_atr(), calculate_rolling_std(),
          calculate_volatility_ratio(), calculate_parkinson_volatility()

[x] I2.3 Implementar src/features/zscore.py
    Entregável: Z-score de retornos
    Critério: Normalização correta + threshold signals
    Tempo: 1h
    NOTA: Implementado com calculate_zscore(), add_zscore_features(),
          calculate_zscore_threshold() (threshold=1.5 default)
```

#### Trilha J: Dataset Unificado (Sequencial)
```
[x] J2.1 Alinhamento temporal UTC
    Entregável: src/features/alignment.py
    Critério: Timestamps consistentes minério + VALE3
    Depende de: I2.1, I2.2, I2.3
    Tempo: 2h
    NOTA: Implementado com create_analysis_dataset(), forward_fill_gaps(),
          filter_trading_days(), add_lagged_features(),
          calculate_lead_lag_correlation(), validate_alignment()

[~] J2.2 Criar dataset consolidado para análise
    Entregável: Tabela analysis_dataset no Supabase ou Parquet local
    Critério: Pronto para testes estatísticos
    Depende de: J2.1
    Tempo: 1h
    NOTA: Função create_analysis_dataset() implementada em alignment.py
          Falta: persistir no Supabase ou exportar para Parquet
```

### Dias 10-11: Testes Estatísticos

#### Trilha K: Análises de Causalidade `||`
```
[ ] K2.1 Notebook: Correlação com lags
    Entregável: notebooks/02_correlation_lags.ipynb
    Critério: Correlações por lag documentadas (1h, 4h, sessão)
    Depende de: J2.2
    Tempo: 2h

[ ] K2.2 Notebook: Teste de Granger Causality (Avançado)
    Entregável: notebooks/03_granger_causality.ipynb
    Critério: Granger + Rolling Granger + Transfer Entropy
    Conteúdo:
      - Granger padrão com múltiplos lags
      - Rolling Granger (janela 60 dias) para verificar estabilidade
      - Transfer Entropy (pyinform) para capturar não-linearidades
      - Comparar TE(minério→VALE3) vs TE(VALE3→minério)
    Depende de: J2.2
    Tempo: 4h
    NOTA: Ver seção "Limitações do Granger" no GUIA_VALIDACAO_ESTATISTICA.md

[ ] K2.3 Notebook: Cointegração Johansen
    Entregável: notebooks/04_cointegration.ipynb
    Critério: Vetor cointegrador se aplicável
    Depende de: J2.2
    Tempo: 2h

[ ] K2.4 Notebook: Análise por subperíodo e regime
    Entregável: notebooks/05_subperiod_stability.ipynb
    Critério: Resultados em 3+ períodos + detecção de mudança de regime
    Conteúdo:
      - Dividir em: 2021, 2022 (crise), 2023-2024, 2025
      - Calcular Granger em cada subperíodo separadamente
      - Implementar detecção de regime (KS-test + vol ratio)
      - Documentar se relação é estável ou varia com regime
    Depende de: J2.2
    Tempo: 3h
    NOTA: Ver seção "Detecção de Regime" no GUIA_VALIDACAO_ESTATISTICA.md
```

### Dias 12-14: Backtest Walk-Forward e Validação de Threshold

#### Trilha L: Backtest Walk-Forward Estruturado (Sequencial)
```
[x] L2.1 Implementar src/strategy/signal_generator.py
    Entregável: Estratégia 1 (rule-based)
    Critério: Sinais LONG/SHORT/NEUTRAL
    Depende de: K2.1
    Tempo: 3h
    NOTA: Implementado com lógica completa:
          - Retorno > 1.5*std → LONG, < -1.5*std → SHORT
          - Filtros: VIX > 25, correlação < 0.2, direção consistente
          - Salva no Supabase e notifica via Telegram

[ ] L2.2 Implementar src/backtest/walk_forward.py
    Entregável: Motor de backtest walk-forward ROLLING
    Critério: Configuração 18m treino / 3m teste / roll 3m
    Conteúdo:
      - Mínimo 8 períodos out-of-sample
      - Custos de transação: 0.30% (conservador, inclui slippage)
      - Métricas por fold: Sharpe, win rate, max DD, trades
      - Função de validação de consistência entre folds
    Depende de: L2.1
    Tempo: 5h
    NOTA: Ver seção "Walk-Forward" no GUIA_VALIDACAO_ESTATISTICA.md

[ ] L2.3 Implementar src/validation/threshold_selection.py
    Entregável: Seleção de threshold com cross-validation
    Critério: Escolha justificada estatisticamente (não arbitrária)
    Conteúdo:
      - Candidatos: 1.0, 1.25, 1.5, 1.75, 2.0 (apenas 5 opções)
      - Time Series Cross-Validation para cada threshold
      - Calcular Deflated Sharpe Ratio (López de Prado)
      - Documentar número total de testes realizados
    Depende de: L2.2
    Tempo: 3h
    NOTA: Ver seção "Threshold" no GUIA_VALIDACAO_ESTATISTICA.md
          IMPORTANTE: Máximo 30 variações de parâmetros para 5 anos de dados

[ ] L2.4 Notebook: Backtest walk-forward completo
    Entregável: notebooks/06_backtest_walkforward.ipynb
    Critério: Sharpe, win rate, max DD após custos (0.30%)
    Conteúdo:
      - Executar walk-forward com threshold selecionado
      - Gráfico de equity curve por fold
      - Tabela de métricas por período
      - Verificar se Sharpe positivo em >70% dos folds
    Depende de: L2.2, L2.3
    Tempo: 3h

[ ] L2.5 Notebook: Sensitivity analysis
    Entregável: notebooks/07_sensitivity.ipynb
    Critério: Robustez a variações de parâmetros
    Conteúdo:
      - Testar thresholds vizinhos (±0.25 do escolhido)
      - Testar janelas de volatilidade (15, 20, 25 dias)
      - Documentar se pequenas mudanças causam grandes variações
      - Se sim → possível overfitting
    Depende de: L2.4
    Tempo: 2h
```

#### Trilha M: Documentação de Decisão (Sequencial)
```
[ ] M2.1 Compilar relatório de decisão GO/NO-GO
    Entregável: docs/decision_gate_week2.md
    Critério: Todos os critérios avaliados objetivamente
    Conteúdo:
      - Resumo dos testes estatísticos (Granger, TE, Cointegração)
      - Resultados do walk-forward por fold
      - Deflated Sharpe Ratio calculado
      - Número total de testes realizados
      - Decisão final justificada
    Depende de: K2.1, K2.2, K2.3, K2.4, L2.4, L2.5
    Tempo: 2h
```

### GATE 1: Decisão GO/NO-GO (Fim da Semana 2)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                           GATE GO/NO-GO                                ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  CRITÉRIOS ESTATÍSTICOS (ver GUIA_VALIDACAO_ESTATISTICA.md):          ║
║                                                                        ║
║  [ ] Walk-forward com pelo menos 8 períodos out-of-sample             ║
║  [ ] Sharpe médio > 1.0 nos períodos de teste                         ║
║  [ ] Sharpe positivo em > 70% dos períodos                            ║
║  [ ] Granger significativo (p < 0.05) em 2+ lags                      ║
║  [ ] Rolling Granger significativo em > 60% das janelas               ║
║  [ ] Deflated Sharpe Ratio > 50% (resultado não é sorte)              ║
║  [ ] Testamos menos de 30 variações de parâmetros                     ║
║                                                                        ║
║  CRITÉRIOS DE ROBUSTEZ:                                               ║
║                                                                        ║
║  [ ] Transfer Entropy minério→VALE3 > VALE3→minério                   ║
║  [ ] Correlação defasada > 0.3 em múltiplos subperíodos               ║
║  [ ] Max drawdown backtest < 15%                                      ║
║  [ ] Win rate > 50%                                                   ║
║  [ ] Estabilidade em 2+ regimes diferentes                            ║
║  [ ] Sensitivity analysis não mostra fragilidade                      ║
║                                                                        ║
║  CRITÉRIOS NO-GO (QUALQUER UM cancela):                               ║
║                                                                        ║
║  [ ] Nenhuma significância estatística                                ║
║  [ ] Sharpe < 0.5 após custos                                         ║
║  [ ] Deflated Sharpe < 50% (resultado é provavelmente sorte)          ║
║  [ ] Inversão de sinal entre subperíodos                              ║
║  [ ] Relação invertida (Vale lidera minério)                          ║
║  [ ] Mais de 30 variações testadas (overfitting provável)             ║
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

#### Trilha T-bis: Reconciliação (Novo)
```
[ ] T3.4 Implementar src/operations/reconciliation.py
    Entregável: Script de reconciliação diária
    Critério: Compara posições Supabase vs MT5
    Conteúdo:
      - Função reconcile_positions(): compara qty, direção, preço médio
      - Função reconcile_orders(): verifica se ordens do dia batem
      - Alertas para discrepâncias
      - Log de reconciliação no Supabase
    Tempo: 3h
    NOTA: Ver seção "Reconciliação" no GUIA_VALIDACAO_ESTATISTICA.md

[ ] T3.5 Configurar reconciliação automática via GitHub Actions
    Entregável: .github/workflows/reconciliation.yml
    Critério: Roda 2x/dia (09:00 e 18:00 BRT)
    Conteúdo:
      - Chama reconciliation.py
      - Envia alerta Telegram se discrepância
      - Pausa novas operações se discrepância crítica
    Depende de: T3.4
    Tempo: 1h
```

#### Trilha T-ter: Versionamento de Modelo (Novo)
```
[ ] T3.6 Implementar src/operations/model_versioning.py
    Entregável: Sistema de versionamento de modelo
    Critério: Registra versão, parâmetros, métricas
    Conteúdo:
      - Tabela model_versions no Supabase
      - Função register_version(): salva snapshot do modelo
      - Função compare_versions(): compara métricas
      - Função rollback_version(): volta para versão anterior
    Tempo: 2h
    NOTA: Ver seção "Versionamento de Modelo" no GUIA_VALIDACAO_ESTATISTICA.md

[ ] T3.7 Criar migração para tabelas de versionamento
    Entregável: sql/004_model_versioning.sql
    Critério: Tabelas model_versions, model_performance
    Conteúdo:
      - model_versions: id, version, commit_hash, params_json, created_at
      - model_performance: id, version_id, period, sharpe, win_rate, max_dd
    Depende de: T3.6
    Tempo: 30min
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
[ ] Reconciliação funcionando (novo)
[ ] Sistema de versionamento configurado (novo)
```

---

## SEMANA 4: Testes Finais, Dashboard e Go-Live

### Dias 22-24: Produção GitHub Actions + Paper Trading

#### Trilha U: Configuração Produção GitHub Actions `||`
```
[x] U4.1 Workflows de coleta já configurados
    Entregável: .github/workflows/daily-tasks.yml
    Critério: Coleta diária rodando
    NOTA: Já implementado na Semana 1

[ ] U4.2 Workflow de geração de sinais (janela crítica)
    Entregável: .github/workflows/signal-generation.yml
    Critério: Roda 09:00-10:00 BRT
    Conteúdo:
      - Cron: "55 11 * * 1-5" (08:55 BRT, seg-sex)
      - Executa: python -m src.strategy.signal_generator
      - Salva sinal no Supabase
      - Notifica via Telegram
    Tempo: 1h

[ ] U4.3 Workflow de monitoramento de saúde
    Entregável: .github/workflows/health-check.yml
    Critério: Verifica conectividade e dados
    Conteúdo:
      - Cron: a cada 4 horas
      - Verifica: Supabase online, dados não stale
      - Alerta Telegram se problema
    Tempo: 30min

[ ] U4.4 Secrets configurados no GitHub
    Entregável: Todos os secrets necessários
    Critério: SUPABASE_URL, SUPABASE_KEY, TELEGRAM_*, LSEG_*
    Tempo: 15min

NOTA: Execução de ordens permanece no PC local com MT5.
      GitHub Actions apenas para coleta e sinais.
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
║  [ ] GitHub Actions rodando workflows (coleta + sinais)               ║
║  [ ] MT5 conectado à conta Clear-Real                                 ║
║  [ ] Telegram bot respondendo comandos                                ║
║                                                                        ║
║  ESTATÍSTICO (ver GUIA_VALIDACAO_ESTATISTICA.md):                     ║
║  [ ] Walk-forward com 8+ períodos validado                            ║
║  [ ] Deflated Sharpe Ratio > 50%                                      ║
║  [ ] Menos de 30 variações testadas                                   ║
║  [ ] Versão do modelo registrada                                      ║
║                                                                        ║
║  TÉCNICO:                                                              ║
║  [ ] Paper trading 5+ dias sem erros                                  ║
║  [ ] Kill switches testados                                           ║
║  [ ] Alertas funcionando                                              ║
║  [ ] Dashboard mostrando métricas                                     ║
║  [ ] Reconciliação testada e sem discrepâncias                        ║
║                                                                        ║
║  RISCO:                                                                ║
║  [ ] Position sizing validado                                         ║
║  [ ] Stop loss testado em demo                                        ║
║  [ ] Daily loss limit testado                                         ║
║  [ ] Comando /kill testado                                            ║
║  [ ] Detecção de regime configurada                                   ║
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

| Serviço | Custo | Notas |
|---------|-------|-------|
| Supabase | Grátis | Free tier: 500MB, 2GB transfer |
| GitHub Actions | Grátis | Free tier: 2000 min/mês |
| Clear | Grátis | Corretagem zero |
| Telegram | Grátis | API gratuita |
| LSEG Workspace | Grátis | Assinatura existente |
| **Total** | **R$0/mês** | 100% gratuito |

**Nota**: Migração de Railway para GitHub Actions eliminou custo mensal.

---

## Histórico de Atualizações

| Data | Versão | Mudança |
|------|--------|---------|
| 2026-01-XX | 1.0 | Criação inicial |
| 2026-01-XX | 2.0 | Migração para Supabase + Railway + Clear |
| 2026-01-16 | 2.1 | Trilha D implementada (LSEG Workspace) |
| 2026-01-16 | 2.2 | Scheduling em Fases (GitHub Actions + LSEG) |
|            |     | - H1.1: src/data/backfill.py com VALE3 |
|            |     | - L2.1: src/strategy/signal_generator.py |
|            |     | - Workflow collect-realtime.yml (Fase 2) |
|            |     | - docs/SECRETS.md |
| 2026-01-16 | 2.3 | Backfill 5 anos + Análise Estatística |
|            |     | - Minério SGX SZZFc2 (front month): 1,300 registros |
|            |     | - VALE3/USD/VIX via Yahoo: 1,758 registros |
|            |     | - Normalização: forward fill + filtro B3 |
|            |     | - Correlação retornos: 0.4354 |
|            |     | - Granger significativo (p < 0.02) |
|            |     | - notebooks/01_exploratory_analysis.ipynb |
|            |     | - SEMANA 1 CONCLUÍDA ✅ |
| 2026-01-16 | 3.0 | Migração Railway → GitHub Actions + Validação Avançada |
|            |     | - Stack atualizada: custo R$0/mês |
|            |     | - docs/GUIA_VALIDACAO_ESTATISTICA.md (novo) |
|            |     | - Semana 2: Walk-Forward estruturado (18m/3m) |
|            |     | - Semana 2: Deflated Sharpe Ratio (López de Prado) |
|            |     | - Semana 2: Transfer Entropy + Rolling Granger |
|            |     | - Semana 2: Detecção de regime (KS-test) |
|            |     | - Semana 2: Validação de threshold (CV) |
|            |     | - Semana 3: Reconciliação diária (novo) |
|            |     | - Semana 3: Versionamento de modelo (novo) |
|            |     | - Gate GO/NO-GO expandido com critérios estatísticos |
|            |     | - Custo transação: 0.30% (conservador) |
| 2026-01-16 | 3.1 | Correção bugs notebook + Validação Granger |
|            |     | - BUG 1: expiry_date filtrava 100% do backfill (NULL) |
|            |     | - BUG 2: Supabase retornava max 1000 rows (paginação) |
|            |     | - SZZFc2 é rolling chain, não precisa de expiry_date |
|            |     | - Corrigido: 01_exploratory_analysis.ipynb células 4 e 6 |
|            |     | - Dataset completo: 1,243 obs (2021-01 a 2026-01) |
|            |     | - Granger Lag 1: p=0.0058 *** (SIGNIFICATIVO) |
|            |     | - Granger Lag 4: p=0.0044 *** (MAIS SIGNIFICATIVO) |
|            |     | - Hipótese central VALIDADA: minério → VALE3 |
| 2026-01-16 | 3.2 | Trilha I/J - Feature Engineering implementada |
|            |     | - src/features/returns.py (retornos, momentum, lagged) |
|            |     | - src/features/volatility.py (ATR, rolling std, ratio) |
|            |     | - src/features/zscore.py (z-score, threshold signals) |
|            |     | - src/features/alignment.py (temporal alignment, ffill) |

---

## Progresso Atual

### Implementado (Trilha I - Feature Engineering)
- `src/features/returns.py` - Retornos 1d/5d/10d/20d, momentum, lagged
- `src/features/volatility.py` - ATR, rolling std, volatility ratio
- `src/features/zscore.py` - Z-Score normalização, threshold signals
- `src/features/alignment.py` - Alinhamento temporal, forward fill, lead-lag

### Implementado (Trilha D - Dados via LSEG)
- `jobs/config/settings.py` - Configurações centralizadas
- `jobs/clients/supabase_client.py` - Cliente Supabase
- `jobs/ingestion/fetch_iron_ore.py` - Coleta 12 contratos futuros SGX
- `jobs/ingestion/fetch_vale3.py` - Coleta VALE3.SA
- `jobs/ingestion/fetch_auxiliary.py` - Coleta USD/BRL
- `jobs/scripts/collect_all.py` - Script de coleta manual
- `sql/003_add_futures_fields.sql` - Migração para variable_key

### Implementado (Backfill Histórico 5 Anos)
- `jobs/ingestion/backfill_historical.py` - Backfill com LSEG + Yahoo
- **Fonte Minério**: LSEG SGX `SZZFc2` (front month contínuo)
- **Fonte VALE3/USD/VIX**: Yahoo Finance
- `notebooks/01_exploratory_analysis.ipynb` - Análise exploratória completa

### Resultados da Análise Estatística (5 Anos)
```
╔══════════════════════════════════════════════════════════════╗
║  RESULTADOS - SGX SZZFc2 vs VALE3                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Período: 2021-01-18 a 2026-01-15 (1,243 observações)       ║
║                                                              ║
║  CORRELAÇÕES:                                                ║
║  • Preços:   0.6493                                         ║
║  • Retornos: 0.4358                                         ║
║  • Rolling (20d): 0.4111 (média)                            ║
║                                                              ║
║  TESTE DE GRANGER (Minério → VALE3):                        ║
║  • Lag 1: p = 0.0058 *** (SIGNIFICATIVO)                    ║
║  • Lag 2: p = 0.0148 ** (SIGNIFICATIVO)                     ║
║  • Lag 4: p = 0.0044 *** (MAIS SIGNIFICATIVO)               ║
║                                                              ║
║  CONCLUSÃO: Minério SGX GRANGER-CAUSA VALE3 ✅               ║
║             Hipótese central VALIDADA com 5 anos de dados   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Normalização de Dados Implementada
- **Forward Fill**: Repete último valor quando mercado fechado (SGX ou B3)
- **Filtro B3**: Só considera dias com cotação de VALE3 (dias de decisão)
- **Alinhamento Temporal**: Minério D0 fecha às 09:00 BRT, VALE3 abre às 10:00 BRT
  → Settlement do minério está disponível 1h antes de VALE3 abrir
- **Alinhamento**: Merge por data, ignora hora

### Fontes de Dados Finais
| Dado | Fonte | RIC/Ticker | Registros |
|------|-------|------------|-----------|
| Minério Fe 62% | LSEG (SGX) | `SZZFc2` | 1,300 |
| VALE3 | Yahoo Finance | `VALE3.SA` | 1,758 |
| USD/BRL | Yahoo Finance | `BRL=X` | 1,305 |
| VIX | Yahoo Finance | `^VIX` | 1,305 |

### Arquitetura de Scheduling
```
FASE 1 (Semanas 1-2): Validação Estatística
├── daily-tasks.yml (06:00 UTC, 1x/dia)
│   └── python -m src.data.backfill --days 1
└── Dados para: Granger, Correlação, Backtest

FASE 2 (Semanas 3-4): Operação (SE GO)
├── collect-realtime.yml (*/15 11-14 UTC, janela crítica)
│   ├── jobs/scripts/collect_all.py --mode realtime
│   └── python -m src.strategy.signal_generator
└── Alertas via Telegram
```

### Próximos Passos Recomendados
1. ~~**Trilhas I, J** - Feature engineering e dataset unificado~~ ✅
2. **J2.2** - Persistir dataset consolidado (Supabase ou Parquet)
3. **Trilha K** - Notebooks de validação (correlação lags, cointegração)
4. **Trilha L** - Backtest walk-forward
5. **GATE GO/NO-GO** - Decisão baseada nos resultados

---

*Documento atualizado para arquitetura simplificada com serviços gerenciados.*
