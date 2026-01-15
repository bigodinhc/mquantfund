# CLAUDE.md — Contexto do Projeto para Claude

Este arquivo fornece contexto para Claude AI ao trabalhar neste projeto.

---

## O Que é Este Projeto

Sistema de trading quantitativo que explora a hipótese de que variações nos preços de futuros de minério de ferro (SGX/DCE, mercado asiático) podem prever movimentos de VALE3 (B3, mercado brasileiro).

**Status atual**: Fase de desenvolvimento/implementação.
**Stack**: Supabase + Railway + GitHub + Clear (MT5)

---

## Arquivos Importantes

| Arquivo | Descrição | Quando Consultar |
|---------|-----------|------------------|
| `roadmap-fundo-quant-vale3-4semanas.md` | Roadmap consolidado completo | Decisões de arquitetura, estratégias, gestão de risco |
| `TRACK.md` | Tarefas semanais detalhadas | Próximos passos, dependências entre tarefas |
| `README.md` | Visão geral do projeto | Setup, estrutura de diretórios |

---

## Estrutura de Código

```
src/
├── data/           # Conectores para coleta de dados
├── features/       # Feature engineering (retornos, volatilidade, etc.)
├── strategy/       # Geração de sinais de trading
├── backtest/       # Motor de backtesting
├── execution/      # Integração com MT5 para execução
├── risk/           # Gestão de risco (sizing, stops, kill switches)
├── scheduler/      # Jobs agendados (coleta de dados)
└── dashboard/      # Interface Streamlit
```

---

## Decisões Técnicas Importantes

### Stack Escolhida
- **Python 3.11+**: Linguagem principal
- **Supabase**: PostgreSQL gerenciado (grátis, free tier)
- **Railway**: Backend Python 24/7 (~R$25-50/mês)
- **GitHub**: Repositório e CI/CD
- **Clear**: Corretora com MT5 (corretagem zero)
- **MetaTrader 5**: Execução de ordens (PC local Windows)
- **APScheduler**: Agendamento de jobs
- **Loguru**: Logging
- **Telegram Bot**: Alertas e comandos (/kill, /status)
- **Streamlit**: Dashboard

### Por que esta stack?
- **Sem Docker**: Supabase fornece PostgreSQL gerenciado
- **Baixo custo**: ~R$25-50/mês total
- **Clear > XP**: Mais popular na comunidade quant brasileira
- **PC local para MT5**: MT5 requer Windows, execução local

### Padrões de Código
- Usar type hints em todas as funções
- Docstrings no formato Google
- Testes com pytest
- Logging com loguru (não print())
- Configuração via variáveis de ambiente (.env)

### Convenções de Nomenclatura
- Classes: `PascalCase` (ex: `IronOreFetcher`)
- Funções/métodos: `snake_case` (ex: `get_latest_price`)
- Constantes: `UPPER_SNAKE_CASE` (ex: `MAX_POSITION_PCT`)
- Arquivos: `snake_case.py`

---

## Horários de Mercado (Crítico)

```
HORÁRIOS (BRT - Brasília)

DCE (Dalian, China):    22:00-04:00 (D-1)
SGX T-Session:          20:25-09:00
SGX T+1 Session:        09:00-17:45
B3 (Brasil):            10:00-17:55

JANELA CRÍTICA: 09:00-10:00 BRT (1h para processar sinal)
```

---

## Regras de Negócio Importantes

### Estratégia Principal (Rule-Based)
```python
# Entrada LONG
if retorno_minerio > 1.5 * desvio_padrao_20d:
    if direção_consistente_2h and usd_brl_variacao < 0.5%:
        signal = "LONG"

# Entrada SHORT
if retorno_minerio < -1.5 * desvio_padrao_20d:
    if direção_consistente_2h and usd_brl_variacao < 0.5%:
        signal = "SHORT"
```

### Critérios de NO-TRADE
- VIX > 25
- Feriado em BR, SG ou CN
- Gap abertura B3 > 2%
- Correlação rolling 20d < 0.2
- Dentro de 2h de anúncio macro

### Position Sizing
```python
risco_por_trade = 0.015 a 0.02  # 1.5-2% do capital
stop_loss = 2 * ATR_14
tamanho_posicao = risco_maximo / stop_loss
# Nunca > 20% da conta em uma posição
```

### Limites de Perda
| Período | Limite | Ação |
|---------|--------|------|
| Diário | 2.5% | HALT automático |
| Semanal | 5% | Reduzir sizing 50% |
| Mensal | 10% | Cessar 5 dias |
| Drawdown | 20% | FULL STOP |

---

## Comandos Úteis

```bash
# Executar testes
pytest tests/ -v

# Verificar tipos
mypy src/

# Formatar código
black src/ tests/
ruff check src/ tests/

# Executar coleta de dados (local)
python -m src.scheduler.jobs

# Paper trading
python -m src.main_loop --mode paper

# Trading real
python -m src.main_loop --mode live

# Dashboard local
streamlit run src/dashboard/app.py

# Testar conexão Supabase
python -c "from supabase import create_client; print('OK')"

# Testar conexão MT5
python -c "import MetaTrader5 as mt5; print(mt5.initialize())"
```

**Deploy Railway**: Push para GitHub → Railway deploya automaticamente

---

## Quando Estiver Implementando

### Ao Criar Novos Módulos

1. Adicionar `__init__.py` no diretório
2. Importar classes/funções principais no `__init__.py`
3. Criar testes correspondentes em `tests/`
4. Usar logging com `from loguru import logger`

### Ao Trabalhar com Dados

1. Sempre converter timestamps para UTC
2. Verificar staleness dos dados antes de usar
3. Salvar dados raw antes de processar
4. Documentar fontes de dados

### Ao Implementar Execução

1. SEMPRE testar em conta DEMO primeiro
2. Implementar retry com backoff exponencial
3. Logar TODAS as ordens (entrada, modificação, saída)
4. Verificar limites de risco ANTES de enviar ordem

### Ao Implementar Risco

1. Kill switches devem ter fallback manual
2. Alertas Telegram para eventos críticos
3. Limites devem ser enforced no código, não apenas logados
4. Nunca confiar apenas em stops do broker

---

## Perguntas Frequentes

### Por que Supabase e não PostgreSQL local?
Supabase é PostgreSQL gerenciado, grátis no free tier (500MB, 2GB transfer). Elimina necessidade de Docker e manutenção de banco.

### Por que Railway?
Railway permite rodar Python 24/7 por ~R$25-50/mês. Deploy automático via GitHub. Alternativa seria VPS (~R$50-100/mês).

### Por que Clear e não XP?
Clear é mais popular na comunidade quant brasileira, API MT5 mais testada, mesma corretagem zero.

### Por que não usar LSTM/redes neurais?
Requer mais dados e é propenso a overfitting com dataset limitado. Para MVP, modelos simples são preferíveis.

### Por que Yahoo Finance e não dados pagos?
Para MVP com capital pequeno (R$20-50k), dados delayed são aceitáveis. Latência de 15-20min não é crítica para estratégia de holding 1-5 dias.

### Por que MT5 no PC local?
MT5 requer Windows. Railway roda Linux. Execução de ordens precisa do MT5 rodando localmente.

### Qual o prazo máximo para validação?
Gate GO/NO-GO no fim da Semana 2. Se critérios não forem atendidos, projeto é arquivado ou pivotado.

---

## Avisos Críticos

1. **NUNCA** hardcode credenciais no código
2. **NUNCA** fazer push de .env para git
3. **NUNCA** executar em modo live sem paper trading
4. **NUNCA** desabilitar kill switches
5. **SEMPRE** verificar mercado aberto antes de operar
6. **SEMPRE** validar dados antes de gerar sinais
7. **SEMPRE** logar todas as decisões de trading

---

## Links de Referência

### Documentação
- [MetaTrader5 Python](https://www.mql5.com/en/docs/python_metatrader5)
- [TimescaleDB](https://docs.timescale.com/)
- [Statsmodels (Granger, Cointegration)](https://www.statsmodels.org/)
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)

### Dados
- [Yahoo Finance](https://finance.yahoo.com/) - Minério de ferro
- [Investing.com](https://www.investing.com/) - Backup minério
- [SGX](https://www.sgx.com/) - Futuros minério
- [B3](https://www.b3.com.br/) - VALE3

---

## Contato e Suporte

Para dúvidas sobre o projeto, consulte:
1. `roadmap-fundo-quant-vale3-4semanas.md` para decisões de arquitetura
2. `TRACK.md` para status das tarefas
3. Issues no repositório para bugs/features

---

## Changelog do Projeto

| Data | Evento |
|------|--------|
| 2026-01-XX | Criação do projeto e documentação inicial |

---

*Este arquivo deve ser atualizado conforme o projeto evolui.*
