# Sistema de Trading Quantitativo: Minério de Ferro × VALE3

**Aviso crítico inicial**: Este relatório trata a relação lead-lag entre futuros de minério de ferro e VALE3 como uma **hipótese a ser validada**, não como fato estabelecido. A pesquisa acadêmica **não encontrou estudos publicados específicos** sobre esta relação preditiva. Qualquer implementação deve ser precedida de validação estatística rigorosa.

A proposta de explorar informação temporal dos futuros de minério de ferro asiáticos para antecipar movimentos da VALE3 no pregão brasileiro seguinte baseia-se em uma premissa lógica—Vale deriva **~80% de sua receita** de soluções de minério de ferro—mas correlação fundamental não implica previsibilidade de mercado. Este relatório examina criticamente cada componente necessário para validar, implementar e operar tal sistema, apresentando **alternativas tecnológicas**, **cenários de falha** e **critérios objetivos** para abandonar a estratégia se a hipótese se mostrar inválida.

---

## A hipótese carece de validação acadêmica publicada

A pesquisa extensiva em literatura acadêmica **não encontrou estudos peer-reviewed** examinando especificamente relações lead-lag entre futuros de minério SGX/DCE e ações da Vale. Isto é significativo: a ausência de validação acadêmica aumenta o risco de correlação espúria e sugere que a hipótese é exploratória, não confirmatória.

**Evidências indiretas encontradas** incluem correlações descritivas mencionadas em comentários de investimento (Seeking Alpha nota "correlação histórica forte" entre Vale e metais base) e observações que o fluxo de caixa trimestral da Vale e preços chineses de minério são "geralmente muito correlacionados". Porém, estas são observações descritivas de fontes não-acadêmicas, não análises estatísticas rigorosas. A literatura mais ampla sobre relações commodity-equity mostra que tais correlações são **fracas, variáveis no tempo e dependentes de regime**—frequentemente desaparecendo em testes out-of-sample.

A janela temporal entre mercados cria oportunidade teórica: o SGX fecha às **12:00 UTC** enquanto a B3 abre às **13:00 UTC**, um gap de apenas 1 hora. A sessão T+1 do SGX (12:15-20:45 UTC) sobrepõe significativamente o horário da B3 (13:00-21:00 UTC), proporcionando descoberta de preços quase contínua. Esta estrutura temporal torna o lead-lag plausível mas não garantido.

| Mercado | Horário Local | Horário UTC | Observação |
|---------|---------------|-------------|------------|
| DCE dia | 09:00-15:00 Beijing | 01:00-07:00 | 6h antes B3 |
| SGX T-Session | 07:25-20:00 Singapore | 23:25(D-1)-12:00 | Gap 1h para B3 |
| B3 regular | 10:00-17:55 Brasília | 13:00-20:55 | Sobrepõe SGX T+1 |
| NYSE VALE ADR | 09:30-16:00 ET | 14:30-21:00* | Simultaneamente |

*Varia com horário de verão americano.

---

## Validação estatística requer múltiplas abordagens complementares

### Testes de causalidade de Granger apresentam limitações severas

O teste de Granger é amplamente utilizado mas **não prova causalidade verdadeira**—apenas testa se valores defasados de X melhoram previsões de Y além dos próprios lags de Y. Estudos do CEPII com painel de 12 mercados de commodities encontraram **nenhuma causalidade** entre posições baseadas em índices e preços de futuros, confirmando a dificuldade de estabelecer relações preditivas.

**Limitações documentadas incluem**: sensibilidade à seleção de lags; resultados variando com período amostral; ignorância de variáveis omitidas em testes bivariados; baixo poder estatístico (risco de erro Tipo II); e premissa de parâmetros constantes que falha em mercados com mudança de regime.

A abordagem **time-varying Granger causality** de Shi et al. (2020) usando algoritmo recursivo evolutivo oferece resultados mais robustos que janelas rolantes tradicionais e pode capturar relações que existem apenas em períodos específicos—particularmente importante para commodities onde correlações intensificam durante estresse.

### Framework de validação recomendado

**Primeira fase—estabelecer racionalidade econômica**: Por que futuros de minério deveriam liderar VALE3? Hipóteses incluem: assimetria informacional (investidores asiáticos reagem primeiro a notícias de demanda chinesa); bases de investidores diferentes (SGX institucional vs B3 misto); ou simples diferença de horários permitindo informação propagar.

**Segunda fase—análise estatística sequencial**:

1. **Correlação defasada** em múltiplas janelas (1-5 dias, intraday)
2. **Cointegração Johansen** para equilíbrio de longo prazo
3. **Granger bivariado e multivariado** (incluindo USD/BRL, VIX)
4. **VAR com funções impulso-resposta** mostrando como Vale responde a choques
5. **Walk-forward validation** com 60% treino / 20% validação / 20% teste

**Terceira fase—robustez e significância econômica**:
- Deflated Sharpe Ratio ajustando para viés de seleção
- Testes em múltiplos regimes (pré/pós-COVID, alta/baixa volatilidade, bull/bear minério)
- Análise de custos de transação realistas (spread + slippage + taxas)
- Comparação com buy-and-hold e entrada aleatória como benchmarks

### Construção de dataset exige cuidado temporal rigoroso

O alinhamento de fusos horários representa desafio técnico crítico. Pesquisa acadêmica confirma que "informação overnight geralmente se reflete nos retornos de ações dentro da primeira meia hora de trading"—sugerindo que sinais de minério da sessão asiática podem estar incorporados rapidamente na abertura da B3.

**Recomendações práticas**:
- Converter todos timestamps para UTC como convenção única
- Separar retornos overnight de retornos intraday na análise
- Documentar tratamento de feriados não coincidentes (Brasil, Singapura, China têm calendários diferentes)
- Testar sensibilidade dos resultados a diferentes premissas de alinhamento temporal
- Usar dados point-in-time quando disponíveis para evitar look-ahead bias

---

## Três estratégias conceituais com diferentes perfis risco-complexidade

### Estratégia 1: Sistema baseado em regras com limiares

**Conceito**: Gerar sinais quando variação do minério SGX excede limiar estatístico, com filtros de confirmação.

**Componentes de decisão**:
- **Entrada**: Variação minério > 1.5σ da volatilidade histórica de 20 dias
- **Confirmação**: Direção consistente nas últimas 2 horas de SGX; USD/BRL estável (< 0.5% variação)
- **Saída**: Stop ATR 2x; take-profit 1:2 risco:retorno; time-stop 5 dias
- **Critérios de não-trade**: VIX > 25; feriado em qualquer mercado; gap abertura B3 > 2%

**Vantagens**: Transparente; fácil debug; sem risco de overfitting de modelo ML; implementação rápida.

**Desvantagens**: Limiares fixos podem não adaptar a regimes diferentes; potencialmente muitos falsos positivos em mercados laterais.

**Horizonte sugerido**: 1-5 dias de holding.

### Estratégia 2: Modelo preditivo com machine learning

**Conceito**: Treinar modelo supervisionado para prever direção/magnitude de VALE3 baseado em features de minério e variáveis auxiliares.

**Alternativas de modelo** (não prescrever uma única):

| Modelo | Prós | Contras | Quando usar |
|--------|------|---------|-------------|
| Random Forest | Robusto a overfitting; interpreta importância de features | Não captura dependências temporais bem | Baseline inicial |
| XGBoost/LightGBM | Alta performance; regularização embutida | Requer tuning cuidadoso | Após baseline RF |
| LSTM/GRU | Captura padrões sequenciais | Propenso a overfitting; caixa-preta | Se relação temporal complexa |
| Ensemble | Combina vantagens | Maior complexidade operacional | Produção madura |

**Features candidatas**:
- Retorno minério SGX (múltiplas janelas: 1h, 4h, sessão completa)
- Volume relativo SGX vs média móvel
- Spread SGX-DCE
- USD/BRL retorno e volatilidade
- VIX e proxies de risco
- Dia da semana, proximidade de vencimento de contratos

**Validação crítica**: Walk-forward com retreino mensal; Deflated Sharpe Ratio; ablation study removendo features individualmente.

### Estratégia 3: Híbrida quant + texto/sentimento

**Conceito**: Combinar sinais quantitativos de preço com análise de texto para detectar eventos que podem amplificar ou invalidar o sinal de minério.

**Arquitetura em duas camadas**:
1. **Camada base**: Sinal quantitativo (Estratégia 1 ou 2)
2. **Camada de modulação**: Sentimento/eventos ajustam tamanho de posição ou vetam trade

**Fontes de texto monitoradas**:
- Notícias de produção de aço chinês (Xinhua, Caixin, MySteel)
- Comunicados operacionais da Vale
- Notícias regulatórias/políticas brasileiras
- Eventos climáticos afetando portos

**Uso específico de NLP** (veja seção D para avaliação crítica):
- FinBERT para scoring de sentimento (não LLM para evitar alucinação)
- Detecção de anomalias (spike negativo de sentimento = veto no trade)
- Alertas para eventos raros (barragem, greve, acidente)

---

## Arquitetura de sistema real-time para operação de pequeno porte

### Diagrama conceitual do pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PIPELINE DE TRADING VALE3/MINÉRIO                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │  INGESTÃO    │    │  FEATURES    │    │   MODELO/    │                  │
│   │  DE DADOS    │───▶│  ENGINE      │───▶│   REGRAS     │                  │
│   └──────────────┘    └──────────────┘    └──────────────┘                  │
│          │                   │                   │                           │
│    MT5/Cedro API       TimescaleDB/         Python Logic                    │
│    SGX delayed         PostgreSQL           (Estratégia)                    │
│                                                  │                           │
│                                                  ▼                           │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │ MONITORAMENTO│◀───│  EXECUÇÃO    │◀───│   GESTÃO     │                  │
│   │   & ALERTAS  │    │  DE ORDENS   │    │   DE RISCO   │                  │
│   └──────────────┘    └──────────────┘    └──────────────┘                  │
│          │                   │                   │                           │
│    Logs/Grafana/       Broker API           Position Sizing                 │
│    Telegram            (MT5/Cedro)          Stops/Limits                    │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────┐         │
│   │                      KILL SWITCH                              │         │
│   │  [Manual Override] [Loss Limit] [Data Stale] [API Down]      │         │
│   └──────────────────────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Comparação de opções tecnológicas

| Componente | Opção A (MVP) | Opção B (Semi-Pro) | Opção C (Dedicado SGX) |
|------------|---------------|--------------------|-----------------------|
| **Linguagem** | Python | Python | Python/Java |
| **Dados minério** | Delayed + API gratuita | Cedro/MetalpriceAPI | Interactive Brokers |
| **Dados VALE3** | MT5 via XP/Clear | Cedro WebSocket | Cedro + backup |
| **Database** | PostgreSQL | TimescaleDB | TimescaleDB cluster |
| **Fila mensagens** | Não necessário | Redis Streams | RabbitMQ |
| **Execução** | MT5 Python API | Cedro OMS | IB + Cedro |
| **Hospedagem** | Local/VPS barato | VPS São Paulo | Cloud São Paulo |
| **Custo mensal** | R$200-500 | R$1.000-2.000 | R$3.000-5.000 |
| **Timeline MVP** | 4 semanas | 6-8 semanas | 8-12 semanas |

**Recomendação para R$20-50k**: Começar com **Opção A** para validar hipótese antes de investir em infraestrutura. MetaTrader 5 + Python oferece caminho mais rápido para time-to-market com custo mínimo.

### Requisitos de latência e tolerâncias

Este não é um sistema HFT—a estratégia opera na escala de minutos a dias, não microssegundos. Tolerâncias realistas:

| Componente | Latência aceitável | Crítico se exceder |
|------------|-------------------|-------------------|
| Dados minério | < 5 minutos | 15 minutos |
| Cálculo features | < 30 segundos | 2 minutos |
| Geração sinal | < 10 segundos | 1 minuto |
| Submissão ordem | < 5 segundos | 30 segundos |
| Confirmação fill | < 10 segundos | 1 minuto |

**Fallback obrigatório**: Se latência de dados exceder limiar crítico, sistema entra em modo seguro (cancela ordens pendentes, não abre novas posições).

### APIs de corretoras brasileiras

| Corretora | Tipo API | Trading automatizado | Acesso | Custo |
|-----------|----------|---------------------|--------|-------|
| **XP** | REST/WebSocket via Cedro | SmarttBot, plataformas | developer.xpinc.com | Negociar |
| **Clear** | Via MT5, Profit, Tryd | SmarttBot integrado | Plataformas parceiras | Zero corretagem |
| **BTG Pactual** | REST/WebSocket | Via terceiros | developer.btgpactual.com | Negociar |
| **Genial** | Conexão B3 padrão | Via plataformas | Full Trading Participant | Variável |

**Regulamentação CVM**: Não existe "licença de algo trading" específica para varejo. Operação via infraestrutura da corretora, que é responsável por controles pré-trade de risco. Sem restrições para trading automatizado via plataformas como MT5/SmarttBot.

---

## NLP/LLM oferecem valor limitado e riscos significativos

### Avaliação crítica: onde NLP genuinamente agrega valor

A pesquisa revela que aplicações de NLP em trading apresentam **proposta de valor mista**. Experiência documentada de mesa de trading de banco de investimento de NYC mostrou que **>70% dos sinais eram falsos positivos** eliminados rapidamente, mas a limpeza do ruído restante era "onerosa demais para resolver completamente". Aproximadamente **1/3 dos sinais corretos** eram pequenos demais relativamente ao spread bid-offer para serem tradáveis.

**Aplicações com evidência de valor**:

| Aplicação | Valor | Evidência |
|-----------|-------|-----------|
| Detecção de eventos raros | ALTO | Disrupções de supply, acidentes, mudanças regulatórias |
| Sumarização para revisão humana | ALTO | Reduz carga cognitiva sem decisões automatizadas |
| Sentimento como fator adicional | MÉDIO | Bloomberg + ML retornou 42% em ouro vs 25% MACD |
| Sinais diretos de trading | BAIXO | Latência inadequada; muitos falsos positivos |

### Onde LLMs falham em trading

**Problema de alucinação é severo**: Pesquisa acadêmica (Kang & Liu, 2023) demonstra que "LLMs off-the-shelf experienciam sérios comportamentos de alucinação em tarefas financeiras". Para consultas de preço de ações, Llama-3-70B respondeu valores de receita corretamente para apenas **54% das empresas** em 2017, caindo para **6%** em 1995. RAG melhora significativamente a factualidade; few-shot learning tem "efetividade limitada".

**Latência é proibitiva**: HFT reage em milissegundos; processamento LLM adiciona 100ms-10s, tornando-o inadequado para reações a preços rápidas. Feeds Bloomberg/Reuters oferecem latência sub-microssegundo—qualquer vantagem de ser primeiro desaparece com processamento LLM.

**Custos escalam rapidamente**: GPT-4o custa ~$3/milhão tokens input, $15/milhão output. A 100M tokens/mês = $300-1.500 dependendo do modelo. Infraestrutura de news feeds premium (Bloomberg, Reuters) custa $50K-500K/ano.

### Três abordagens recomendadas por perfil de risco

**Abordagem 1 (Baixo Risco)—Serviço de sumarização**:
- FinBERT para scoring de sentimento (não LLM)
- Sumarização diária/semanal usando LLM
- Alertas para anomalias (spike negativo, keywords críticas)
- **Investimento**: R$50-100K/ano
- **Valor**: Suporte a decisão, economia de tempo de analista

**Abordagem 2 (Médio Risco)—Fator de sentimento**:
- Integrar scores de sentimento como fator adicional em modelo quantitativo
- Ablation study rigoroso para validar valor incremental
- Rebalanceamento diário
- **Investimento**: R$200-400K/ano
- **Valor esperado**: Melhoria potencial 5-15% no Sharpe ratio

**Abordagem 3 (Alto Risco)—Trading event-driven**:
- Monitoramento real-time de notícias Vale/minério
- Playbooks pré-definidos por tipo de evento
- Human-in-the-loop para execução
- **Investimento**: R$500K-1M/ano
- **Valor**: Alpha oportunístico em eventos maiores

**Para R$20-50k de capital**: Abordagem 1 é única viável dado orçamento. Abordagens 2-3 requerem escala institucional.

---

## Gestão de risco dimensionada para portfólio de R$20-50k

### Dimensionamento de posição

**Método primário recomendado**: ATR-based volatility sizing com **1.5-2% de risco por trade**.

Para conta de R$50.000:
- Risco máximo por trade: R$750-1.000
- Com stop 2x ATR (assumindo ATR VALE3 ≈ R$1,50, preço ≈ R$60): Stop = R$3,00
- Tamanho posição = R$1.000 / R$3,00 = **333 ações** (≈ R$20.000, ou 40% da conta)

**Kelly Criterion como guia** (não como regra): Com win rate 55% e ratio win/loss 2:1, Kelly sugere 32.5%. Usar **Quarter Kelly (8%)** a **Half Kelly (16%)** como teto, sempre respeitando limites absolutos.

**Limites absolutos independentes de Kelly**:
- Posição única: ≤20% da conta
- Exposição direcional total: ≤50% da conta
- Posições abertas simultâneas: máximo 3

### Controles de stop e take-profit

| Tipo | Parâmetro | Implementação |
|------|-----------|---------------|
| **Stop inicial** | 2x ATR(14) | Calculado na entrada; não mover contra posição |
| **Stop breakeven** | Ao atingir 1x risco | Mover stop para preço de entrada |
| **Trailing stop** | Chandelier Exit 1.5x ATR | Após atingir 2x risco |
| **Take-profit parcial** | 50% em 1x risco | Reduz exposição, garante lucro parcial |
| **Time-stop** | 5 dias úteis | Se posição não progrediu 50% do target |

### Limites de perda em cascata

| Período | Limite | Ação ao atingir |
|---------|--------|-----------------|
| Diário | 2.5% (R$1.250 em R$50k) | Halt automático; zero trades resto do dia |
| Semanal | 5% (R$2.500) | Reduzir tamanho posições 50% na semana seguinte |
| Mensal | 10% (R$5.000) | Cessar trading por 5 dias úteis; revisar estratégia |
| Drawdown máximo | 20% (R$10.000) | Full stop; revalidação completa da hipótese |

### Custos de execução na B3 para VALE3

| Componente | Estimativa | Notas |
|------------|-----------|-------|
| Taxas B3 (emolumentos) | ~0.030% por lado | ~0.06% round-trip |
| Corretagem (Clear/XP) | 0-0.05% | Muitas zero corretagem |
| Spread bid-ask VALE3 | 0.03-0.05% | Mega-cap muito líquida |
| Slippage (ordem <R$50k) | 0.05-0.10% | Impacto de mercado negligenciável |
| **Total round-trip** | **0.15-0.25%** | Orçar 0.25% conservadoramente |

**Implicação para estratégia**: Com custo round-trip de 0.25%, a estratégia precisa gerar retorno médio por trade >0.25% apenas para empatar. Para holding de 1-5 dias, isto representa hurdle significativo.

### Kill switches e controles de falha

```
HIERARQUIA DE KILL SWITCHES:

[Nível 1: Automático - Imediato]
├── Loss limit diário atingido → HALT todas operações
├── Dados stale > 60 segundos → ALERT + cancelar ordens pendentes  
├── Dados stale > 5 minutos → FECHAR posições a mercado
└── 3 ordens rejeitadas em 10 min → PAUSE + investigar API

[Nível 2: Automático - Com confirmação]
├── Divergência preço >2% entre fontes → ALERT + pause para revisão
├── 3 trades perdedores consecutivos → PAUSE 30 minutos
└── Correlação rolling <0.3 por 5 dias → FLAG para revisão manual

[Nível 3: Manual obrigatório]
├── Posição >10% da conta → Requer aprovação manual
├── Override de qualquer safety limit → Requer justificativa documentada
└── Primeiro trade em instrumento novo → Requer teste prévio

[Nível 4: Botão de pânico]
├── Software kill switch → Cancelar tudo + fechar posições
├── Contato emergencial corretora → Número 24h documentado
└── Desligar máquina/VPS → Último recurso
```

---

## Monitoramento, governança e operações diárias

### Métricas de performance e risco

**Métricas de performance (calcular diariamente)**:
- P&L realizado e não-realizado
- Win rate rolling 20 trades
- Profit factor (gross profit / gross loss)
- Average win vs average loss
- Sharpe ratio rolling 30/60/90 dias

**Métricas de risco (monitorar real-time)**:
- Exposição atual (% da conta)
- Distância ao stop (em R$ e %)
- Drawdown atual vs máximo histórico
- Correlação rolling VALE3 vs minério
- VIX/volatilidade implícita de VALE3

**Métricas operacionais (auditar semanalmente)**:
- Slippage médio vs esperado
- Latência média do pipeline
- Taxa de rejeição de ordens
- Uptime do sistema
- Discrepâncias de reconciliação

### Observabilidade: logs, alertas, auditoria

**Logging obrigatório por ordem**:
- Timestamp (precisão milissegundo)
- Order ID interno e da exchange
- Símbolo, lado, quantidade, preço, tipo
- Razão/sinal que gerou a ordem
- Status final e detalhes de fill
- **Retenção**: 5 anos (requisito regulatório)

**Alertas configurados**:

| Evento | Canal | Urgência |
|--------|-------|----------|
| Ordem executada | Log | Baixa |
| Loss limit 50% atingido | Email | Média |
| Loss limit 100% atingido | SMS/Telegram | Alta |
| Dados stale | Telegram | Alta |
| API error | Email + Log | Média |
| Drawdown >15% | SMS | Crítica |

### Checklist operacional diário

**Pré-mercado (antes das 09:30 BRT)**:
- [ ] Verificar status de conexões (MT5, data feeds)
- [ ] Revisar posições abertas overnight
- [ ] Checar calendário (feriados em qualquer mercado?)
- [ ] Verificar notícias relevantes overnight
- [ ] Confirmar capital disponível vs margens

**Durante mercado**:
- [ ] Monitorar dashboard de métricas
- [ ] Verificar execução de ordens
- [ ] Responder a alertas imediatamente

**Pós-mercado (após 18:00 BRT)**:
- [ ] Reconciliar posições (interno vs extrato corretora)
- [ ] Documentar trades do dia com justificativas
- [ ] Calcular métricas diárias
- [ ] Backup de logs e database
- [ ] Revisar erros ou anomalias

### Critérios objetivos para pausar sistema

| Trigger | Ação | Duração pausa |
|---------|------|---------------|
| Drawdown >15% | Revisão parcial | 3 dias úteis |
| Drawdown >20% | Full stop + revalidação | Indefinido até aprovação |
| Win rate <40% em 30 trades | Análise de drift | 5 dias úteis |
| Correlação minério-VALE3 <0.2 por 10 dias | Hipótese questionada | Revalidação estatística |
| 3 meses sem retorno positivo | Sunset da estratégia | Descontinuação |
| Evento Vale tipo Brumadinho | Full stop imediato | Avaliação caso-a-caso |

---

## Plano de implementação em 4 semanas

### Semana 1: Infraestrutura de dados e validação inicial

**Entregáveis verificáveis**:
- [ ] Conta em corretora ativa (XP ou Clear) com MT5 configurado
- [ ] Pipeline de coleta de dados minério SGX funcionando (delayed OK)
- [ ] Pipeline de coleta VALE3 via MT5 funcionando
- [ ] Database PostgreSQL com schema para armazenamento
- [ ] Análise exploratória inicial: correlação descritiva minério × VALE3

**Riscos da semana**: Atraso em aprovação de conta; dificuldade de acesso a dados minério gratuitos.
**Mitigação**: Iniciar processo de conta imediatamente; usar múltiplas fontes de dados como backup.

### Semana 2: Validação estatística e design de estratégia

**Entregáveis verificáveis**:
- [ ] Teste de Granger causality completo (múltiplas janelas de lag)
- [ ] Análise de cointegração Johansen
- [ ] Walk-forward backtest de estratégia baseada em regras
- [ ] Documentação de resultados estatísticos (positivos OU negativos)
- [ ] Decisão go/no-go para continuar implementação

**GO CRITERIA**: Relação lead-lag estatisticamente significativa (p<0.05) em pelo menos 2 janelas temporais diferentes; backtest walk-forward com Sharpe >1.0 após custos.

**NO-GO CRITERIA**: Nenhuma significância estatística; Sharpe <0.5 após custos; relação instável entre subperíodos.

**Riscos da semana**: Validação estatística negativa invalida projeto.
**Mitigação**: Se no-go, documentar aprendizados e considerar hipóteses alternativas (outros pares, outros mercados).

### Semana 3: Sistema de execução e controles de risco

**Entregáveis verificáveis** (se GO na semana 2):
- [ ] Módulo de geração de sinais funcionando
- [ ] Integração com MT5 para submissão de ordens
- [ ] Todos kill switches implementados e testados
- [ ] Controles de position sizing funcionando
- [ ] Paper trading iniciado (sem capital real)

**Riscos da semana**: Bugs na integração com API; paper trading revela problemas não detectados em backtest.
**Mitigação**: Testes extensivos em ambiente de simulação antes de capital real.

### Semana 4: Testes finais, monitoring e go-live gradual

**Entregáveis verificáveis**:
- [ ] Pelo menos 5 dias de paper trading sem erros críticos
- [ ] Dashboard de monitoring funcional
- [ ] Alertas configurados e testados
- [ ] Documentação operacional completa
- [ ] Go-live com 10% do capital planejado (R$2-5k)

**Critérios para escalar capital**:
- 2 semanas de operação sem erros técnicos
- Performance consistente com backtest (±20%)
- Nenhum trigger de pause ativado

**Riscos do projeto**:

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Validação estatística negativa | MÉDIA | Projeto cancelado | Documentar e pivotar |
| Atraso em aprovação de conta | BAIXA | 1-2 semanas delay | Iniciar processo dia 1 |
| Dados minério inacessíveis | BAIXA | Requer alternativas | Múltiplas fontes mapeadas |
| Bugs em execução | MÉDIA | Paper trading estendido | Testes extensivos |
| Capital insuficiente para custos | BAIXA | Escopo reduzido | Opção A (MVP) prioriza baixo custo |

---

## Por que esta estratégia pode falhar: 18 cenários críticos

### Categoria 1: Decaimento de alpha e ciclo de vida da estratégia

**1. Crowding de sinal e competição**
Relações lead-lag são arbitradas quando mais traders descobrem a mesma ineficiência. Pesquisa Maven Securities mostra que custos de decay de alpha totalizam **9.9% anualmente na Europa e 5.6% nos EUA**, com tendência de alta de 16-36 bps por ano.

*Detecção*: Sharpe ratio declinante em janelas rolling; lucro médio por trade reduzindo; slippage aumentando.
*Mitigação*: Monitorar decay via métricas rolling; diversificar fontes de alpha; aceitar vida útil finita da estratégia (12-24 meses).

**2. Desaparecimento da relação lead-lag**
Pesquisa acadêmica (Brooks et al., 2001) demonstra que mesmo quando efeitos lead-lag são estatisticamente identificáveis, trading deles é frequentemente não-lucrativo após custos de transação.

*Detecção*: Correlação defasada não significativa em períodos recentes; lag ótimo instável.
*Mitigação*: Usar métodos de lag dinâmico (Dynamic Time Warping); implementar análise de breakeven estrita.

**3. Novos participantes eliminando ineficiência**
HFT representa **28%+ do volume de futuros** (vs 22% em 2009). Mercado de derivativos de minério está se tornando mais sofisticado.

*Detecção*: Volume eletrônico aumentando; resposta de preço a notícias mais rápida.
*Mitigação*: Investir em execução mais rápida; aceitar vida útil finita da estratégia.

### Categoria 2: Quebra de correlação e mudança de regime

**4. Mudança de regime de correlação commodity-equity**
Pesquisa do BIS mostra que correlações stock-commodity variaram de **-0.39 a 0.76** entre 1962-2012. Correlações disparam durante crises (recessão início dos 80s: 66%; crise 2008: similar).

*Detecção*: VIX spiking; spreads de crédito alargando; mudança rápida no sentimento do setor imobiliário chinês.
*Mitigação*: Algoritmos de detecção de regime (DCC-GARCH); reduzir posição em regimes de alta correlação.

**5. Desacoplamento minério de ferro × ações de mineração**
Ações de mineração podem divergir de preços de commodities devido a fatores específicos da empresa, efeitos cambiais ou mudanças em estrutura de custos.

*Detecção*: Beta da Vale ao minério mudando significativamente; divergência em cobertura de analistas.
*Mitigação*: Monitorar correlação rolling; definir threshold de correlação abaixo do qual estratégia pausa.

**6. Mudança de regime de demanda chinesa**
China responde por **~70% da demanda de minério transportado por mar**. Mudança estrutural na produção de aço chinês invalidaria padrões históricos.

*Detecção*: Ratio sucata-para-aço chinês aumentando; starts imobiliários caindo YoY; estoques portuários construindo.
*Mitigação*: Monitorar fundamentos do setor de aço chinês; considerar sunset da estratégia se mudança estrutural confirmada.

### Categoria 3: Eventos específicos da Vale e cisnes negros

**7. Desastre de barragem / Evento ESG**
O colapso da barragem de Brumadinho (janeiro 2019) causou queda de **24% em um dia** na Vale, perdendo $19 bilhões em valor de mercado—a maior perda de um dia na história da bolsa brasileira.

*Detecção*: Mínima—desastres são inerentemente imprevisíveis.
*Mitigação*: Limites de posição estritos; stops (embora gaps possam ultrapassá-los); hedges de tail-risk (puts em Vale); diversificação.

**8. Volatilidade BRL/USD dominando sinal**
Vale fatura em USD mas reporta em BRL. USD/BRL é um dos pares de moeda mais voláteis do G20.

*Detecção*: Volatilidade implícita BRL spiking; crise política brasileira; mudanças em diferencial de juros.
*Mitigação*: Adicionar filtro de volatilidade BRL/USD; hedgear exposição cambial; considerar spread ADR vs listing brasileiro.

**9. Risco político/regulatório brasileiro**
Vale enfrentou ações regulatórias significativas incluindo proibições operacionais, suspensão de dividendos e multas ambientais.

*Detecção*: Ciclos eleitorais; ações de enforcement ambiental; propostas regulatórias para indústria de mineração.
*Mitigação*: Monitorar news feeds brasileiros; reduzir exposição durante incerteza política.

### Categoria 4: Falhas técnicas e operacionais

**10. Falhas de feed de dados / Preços stale**
Futuros de minério negociam em múltiplas exchanges (Dalian, Singapura, CME) em diferentes fusos. Trading recente de minério mostrou **declínio de 52% no volume em um dia** quando liquidez spot diminuiu.

*Detecção*: Gaps de preço incomuns entre fontes; timestamps atrasando; spreads anormalmente largos.
*Mitigação*: Múltiplos feeds redundantes; detecção de staleness; cross-reference entre exchanges.

**11. Slippage de execução durante baixa liquidez**
Liquidez de ADR Vale depende do horário do mercado americano. Executar durante janelas de baixa liquidez (fechamento asiático para pré-mercado americano) pode resultar em slippage substancial.

*Detecção*: Spreads bid-ask alargando; profundidade do order book reduzindo; períodos de feriado.
*Mitigação*: Limitar trading a janelas de alta liquidez; usar limit orders; modelar slippage esperado por horário.

**12. Downtime de API/infraestrutura em momentos críticos**
Flash crashes e movimentos extremos frequentemente coincidem com sobrecarga de sistemas. CME pode aumentar requisitos de margem subitamente.

*Detecção*: Notificações técnicas da exchange; latência do sistema aumentando; taxa de erro de APIs subindo.
*Mitigação*: Conectividade redundante; kill switch; orders limite pré-posicionadas para saída durante outages.

### Categoria 5: Armadilhas estatísticas e de backtesting

**13. Overfitting de backtest**
Pesquisa de López de Prado mostra que se apenas 5 anos de dados diários estão disponíveis, **não mais que 45 variações de estratégia deveriam ser testadas** para evitar resultados espúrios. Estudo da Quantopian encontrou "correlações muito fracas entre performance in-sample e out-of-sample" (R² < 0.025 para Sharpe ratio).

*Detecção*: Sharpe ratios de backtest >3.0; muitas combinações de parâmetros testadas; performance sensível a pequenas mudanças de parâmetros.
*Mitigação*: Registrar todos testes conduzidos; usar Deflated Sharpe Ratio; limitar graus de liberdade; exigir justificativa econômica para cada parâmetro.

**14. Viés de sobrevivência em backtest**
Testar apenas constituintes atuais de índice ignora empresas deslistadas, falidas ou adquiridas.

*Detecção*: Testar apenas Vale vs minério sem outros pares de mineração; ignorar mudanças históricas de estrutura de mercado.
*Mitigação*: Usar databases livres de survivorship bias; testar lógica em múltiplas empresas de mineração; incluir períodos de estresse.

**15. Subestimação de custos de transação**
Pesquisa mostra que "um backtest mostrando 15% de retorno anual pode colapsar para perto de zero após contabilizar custos realistas, especialmente em estratégias de alta frequência ou alto turnover".

*Detecção*: Turnover da estratégia maior que esperado; custos de execução reais excedendo premissas de backtest.
*Mitigação*: Modelar custos conservadoramente (2x esperado); incluir slippage baseado em fills históricos; adicionar custos de spread explicitamente.

### Categoria 6: Estrutura de mercado e fatores externos

**16. Mudanças de regras de exchange**
CME, SGX e Dalian podem mudar requisitos de margem, horários de trading ou limites de posição com aviso limitado. Crash de prata de dezembro 2025 foi triggered por CME aumentando margens duas vezes em uma semana.

*Detecção*: Consultas regulatórias de exchanges; revisões de limites de posição; mudanças de metodologia de margem.
*Mitigação*: Monitorar anúncios de exchanges; manter margem excess; diversificar entre exchanges.

**17. Mudança macro de regime (cisne negro)**
O superciclo de commodities teve pico em 2011 e não retornou. COVID-19, guerras comerciais e eventos geopolíticos causaram spikes de correlação imprevisíveis.

*Detecção*: Escalação geopolítica; ações de política sem precedentes; mudanças estruturais no comércio global.
*Mitigação*: Manter tamanhos de posição pequenos; usar monitoramento dinâmico de correlação; ter critérios explícitos de shutdown.

**18. Projeto Simandou alterando dinâmica de supply**
Nova capacidade de 120 milhões de toneladas entrando online em 2026-2027 da Guiné pode alterar fundamentalmente equilíbrio de oferta-demanda de minério e invalidar relações históricas.

*Detecção*: Anúncios de progresso do projeto; mudanças na participação de mercado de produtores; pressão de preço de longo prazo.
*Mitigação*: Monitorar publicações da indústria; considerar sunset da estratégia se estrutura de supply mudar fundamentalmente.

---

## Conclusão: uma hipótese a ser validada, não uma estratégia garantida

Este relatório apresentou o design conceitual completo de um sistema de trading explorando a relação temporal entre futuros de minério de ferro e VALE3. A **descoberta mais importante** é que a hipótese central carece de validação acadêmica publicada—nenhum estudo peer-reviewed foi encontrado examinando especificamente esta relação lead-lag.

Isto não significa que a relação não existe, mas implica que qualquer implementação é **exploratória, não confirmatória**. Os 18 modos de falha documentados demonstram que mesmo uma relação estatisticamente válida pode ser não-lucrativa após custos, instável através de regimes, ou arbitrada por competidores.

**Recomendações finais prioritizadas**:

1. **Validação estatística rigorosa** antes de qualquer capital em risco—Semana 2 do plano é ponto de decisão go/no-go

2. **Começar com infraestrutura mínima** (Opção A: ~R$200-500/mês) para preservar capital para trading

3. **Escalar capital gradualmente** (10% → 25% → 50% → 100%) condicionado a performance consistente

4. **Definir critérios de sunset antecipadamente**: 3 meses sem retorno positivo, drawdown >20%, ou correlação <0.2 por 10 dias devem triggerar revalidação ou descontinuação

5. **Documentar tudo**: registrar todas análises estatísticas, trades e decisões para aprendizado independentemente do resultado

A honestidade epistêmica exige reconhecer que a maioria das estratégias quantitativas **não funcionam** após implementação real. O valor deste exercício está tanto em validar uma oportunidade quanto em descobrir, com rigor metodológico, que ela não existe—evitando assim a perda de capital em uma tese inválida.