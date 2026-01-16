# Guia de Validação Estatística para o Fundo Quant

**Objetivo**: Explicar de forma simples os conceitos estatísticos e operacionais que garantem que nossa estratégia de trading é robusta e não fruto de sorte.

**Público**: Leigos em estatística que querem entender o "porquê" por trás de cada decisão.

---

## Índice

1. [Walk-Forward: Testando a Estratégia Como na Vida Real](#1-walk-forward-testando-a-estratégia-como-na-vida-real)
2. [Frequência de Retreino: Quando Atualizar os Parâmetros](#2-frequência-de-retreino-quando-atualizar-os-parâmetros)
3. [Detecção de Regime: Percebendo Quando o Mercado Muda](#3-detecção-de-regime-percebendo-quando-o-mercado-muda)
4. [Threshold: Escolhendo Limites Sem Chutar](#4-threshold-escolhendo-limites-sem-chutar)
5. [Limitações do Teste de Granger: O Que Ele Não Conta](#5-limitações-do-teste-de-granger-o-que-ele-não-conta)
6. [Reconciliação: Verificando Se Tudo Está Certo](#6-reconciliação-verificando-se-tudo-está-certo)
7. [Versionamento de Modelo: Histórico de Mudanças](#7-versionamento-de-modelo-histórico-de-mudanças)

---

## 1. Walk-Forward: Testando a Estratégia Como na Vida Real

### O Problema com Backtests Tradicionais

Imagine que você tem uma prova de matemática amanhã. Você estuda com as provas antigas do professor e decora todas as respostas. No dia da prova, você tira 10. Mas será que você realmente aprendeu matemática, ou apenas decorou as respostas?

O **backtest tradicional** é como decorar as respostas. Você olha para 5 anos de dados históricos, ajusta sua estratégia até ela funcionar perfeitamente nesses dados, e conclui que ela é boa. O problema: você está testando no mesmo dado que usou para criar a estratégia. Isso se chama **overfitting** (sobreajuste).

### A Solução: Walk-Forward

O **Walk-Forward** é como fazer várias provas surpresa ao longo do ano, usando apenas o conteúdo que você já estudou até aquele momento.

Funciona assim:

```
Ano 1     Ano 2     Ano 3     Ano 4     Ano 5
│         │         │         │         │
▼         ▼         ▼         ▼         ▼

[===ESTUDO===][ PROVA ]
              [===ESTUDO===][ PROVA ]
                            [===ESTUDO===][ PROVA ]
                                          [===ESTUDO===][ PROVA ]
```

1. Você "estuda" com os dados do Ano 1-2 (período de treino)
2. Faz uma "prova" no Ano 3 (período de teste) — dados que você nunca viu
3. Anota a nota
4. Avança no tempo: agora estuda com Ano 2-3, faz prova no Ano 4
5. Repete até acabar os dados

No final, você tem várias "notas" de provas que você nunca tinha visto antes. Se todas as notas forem boas, a estratégia provavelmente é robusta. Se algumas forem péssimas, você pode ter sorte em alguns períodos.

### Por Que Isso Importa Para Nós

Nossa estratégia tenta prever VALE3 baseada no minério de ferro. Se fizermos um backtest tradicional, podemos acidentalmente criar uma estratégia que só funcionou no passado por coincidência. Com Walk-Forward:

- Simulamos o que teria acontecido se tivéssemos usado a estratégia desde 2021
- Cada "prova" é um período de 3 meses que nunca foi usado para criar a estratégia
- Se a estratégia funcionar em 70%+ das "provas", temos mais confiança

### Configuração Recomendada

| Parâmetro | Valor | Explicação |
|-----------|-------|------------|
| Período de estudo (treino) | 18 meses | Tempo suficiente para capturar diferentes condições de mercado |
| Período de prova (teste) | 3 meses | Curto o suficiente para ter várias provas, longo para ser estatisticamente relevante |
| Frequência de avanço | 3 meses | A cada 3 meses, "rolamos" a janela para frente |
| Mínimo de provas | 8 | Queremos pelo menos 8 períodos de teste para tirar conclusões |

### Critérios de Aprovação

Para considerarmos a estratégia válida:

- **Sharpe Ratio médio > 1.0**: O retorno ajustado ao risco deve ser bom na média
- **Sharpe positivo em 70%+ das provas**: Não basta ter média boa se metade das provas foi ruim
- **Sem inversão de sinal**: Se a estratégia era de compra em média, não pode ter períodos onde ela perdeu muito vendendo

---

## 2. Frequência de Retreino: Quando Atualizar os Parâmetros

### Analogia: Ajustando o Termostato

Imagine que você tem um ar-condicionado com termostato. No verão, você configura para 22°C. No inverno, talvez 25°C. Você não muda a temperatura toda hora — isso seria instável. Mas também não deixa fixo o ano inteiro — isso seria ineficiente.

Nossa estratégia tem "termostatos" (parâmetros) que precisam ser ajustados com a frequência certa:

### Parâmetros e Suas Frequências

| Parâmetro | O Que É | Frequência de Ajuste | Por Quê |
|-----------|---------|---------------------|---------|
| **Threshold (1.5σ)** | O limite que define quando o movimento do minério é "significativo" | Trimestral | A volatilidade do mercado muda lentamente, ciclos econômicos duram meses |
| **Janela de volatilidade (20 dias)** | Quantos dias usamos para calcular a volatilidade | Mensal | Ciclos de mercado podem mudar em semanas |
| **Stop loss (2x ATR)** | Quanto estamos dispostos a perder por operação | Diário | A volatilidade muda todo dia, nosso stop deve acompanhar |
| **Correlação mínima (0.2)** | Limite de segurança para pausar a estratégia | Nunca | É um limite de segurança fixo, não um parâmetro de otimização |

### Por Que Não Ajustar Tudo Todo Dia?

1. **Overfitting**: Ajustar demais aos dados recentes faz você perseguir ruído, não tendências reais
2. **Custos de transação**: Mudanças frequentes podem gerar mais trades, aumentando custos
3. **Instabilidade**: Parâmetros que mudam muito geram comportamento imprevisível

### Por Que Não Deixar Tudo Fixo?

1. **Mercados mudam**: O que funcionou em 2022 pode não funcionar em 2025
2. **Volatilidade varia**: Em crises, a volatilidade dispara; usar parâmetros de épocas calmas é perigoso
3. **Adaptação**: Estratégias que se adaptam sobrevivem mais tempo

### Regra de Ouro

> Ajuste parâmetros na frequência em que a informação subjacente muda, não na frequência em que você consegue medir.

A volatilidade diária muda todo dia, mas tendências de volatilidade mudam em semanas. Por isso, recalculamos a volatilidade diariamente, mas só ajustamos o threshold trimestralmente.

---

## 3. Detecção de Regime: Percebendo Quando o Mercado Muda

### O Que É Um "Regime" de Mercado?

Pense no clima: temos estações do ano. No verão, faz calor e chove. No inverno, faz frio e seco. Se você usar o mesmo guarda-roupa o ano todo, vai passar frio no inverno ou calor no verão.

O mercado também tem "estações":

| Regime | Características | Exemplo |
|--------|-----------------|---------|
| **Bull Market (alta)** | Preços subindo, volatilidade baixa, otimismo | 2019, 2021 |
| **Bear Market (baixa)** | Preços caindo, volatilidade alta, pessimismo | Março 2020, 2022 |
| **Sideways (lateral)** | Preços estáveis, baixa volatilidade | Períodos de consolidação |
| **Crise** | Quedas abruptas, volatilidade extrema, correlações quebram | COVID-19, Brumadinho |

### Por Que Detectar Regimes?

Nossa estratégia assume que o minério de ferro "lidera" a VALE3. Mas isso pode não ser verdade em todos os regimes:

- **Em regime normal**: Minério sobe → VALE3 sobe no dia seguinte (nossa hipótese)
- **Em crise**: Tudo cai junto, não há "liderança" — todos reagem ao mesmo pânico
- **Em rally especulativo**: VALE3 pode subir por motivos domésticos (câmbio, política), ignorando o minério

Se o mercado muda de regime e não percebemos, nossa estratégia pode:
1. Gerar sinais baseados em uma relação que não existe mais
2. Perder dinheiro sistematicamente
3. Nos dar falsa confiança

### Como Detectamos Mudança de Regime?

Usamos indicadores simples que comparam "como o mercado está agora" vs "como estava antes":

**Indicador 1: Razão de Volatilidade**

Comparamos a volatilidade dos últimos 20 dias com a volatilidade dos últimos 60 dias:

- Se volatilidade recente é 50% maior que a histórica → mercado ficou mais turbulento
- Se volatilidade recente é 50% menor → mercado acalmou

**Indicador 2: Teste de Distribuição**

Verificamos se os retornos recentes "se parecem" com os retornos históricos:

- Se parecem → regime estável
- Se não parecem → algo mudou

**Indicador 3: Correlação Rolling**

Calculamos a correlação entre minério e VALE3 a cada 20 dias:

- Se correlação cai abaixo de 0.2 por 10 dias → a relação pode ter quebrado
- Se correlação fica negativa → a relação inverteu (muito perigoso!)

### O Que Fazemos Quando Detectamos Mudança?

| Nível de Alerta | Condição | Ação |
|-----------------|----------|------|
| **Amarelo** | Volatilidade 50% acima do normal | Reduzir tamanho das posições pela metade |
| **Laranja** | Correlação abaixo de 0.2 por 5 dias | Pausar novos trades, manter posições existentes |
| **Vermelho** | Correlação abaixo de 0.2 por 10 dias OU volatilidade 100% acima | Fechar todas as posições, pausar estratégia |
| **Preto** | Evento extremo (gap > 5%, notícia de desastre) | Kill switch imediato |

### Analogia Final

Detectar regime é como verificar a previsão do tempo antes de sair de casa:

- Céu limpo → saia normalmente
- Nublado → leve um guarda-chuva (reduz exposição)
- Temporal anunciado → fique em casa (pause a estratégia)
- Furacão → evacue (kill switch)

---

## 4. Threshold: Escolhendo Limites Sem Chutar

### O Problema do "Chute Educado"

No roadmap original, definimos que um sinal de compra é gerado quando o minério sobe mais de 1.5 desvios-padrão. Mas por que 1.5? Por que não 1.0, 2.0, ou 1.73?

Se escolhermos o threshold olhando para os dados históricos e vendo qual dá mais lucro, estamos trapaceando. É como fazer uma aposta de loteria depois de saber os números sorteados.

### O Que É Overfitting?

Imagine que você quer prever se vai chover. Você olha para os últimos 100 dias e descobre que:

- "Toda vez que meu vizinho lavou o carro na terça-feira e o céu tinha exatamente 37% de nuvens, choveu no dia seguinte"

Isso pode ser verdade nos seus 100 dias de dados, mas é coincidência. No futuro, essa "regra" não vai funcionar.

**Overfitting** é encontrar padrões que existem apenas nos seus dados de teste, não no mundo real.

### Como Escolher Thresholds Sem Overfitting?

**Método 1: Validação Cruzada Temporal**

Em vez de testar um threshold em todos os dados, testamos em partes separadas:

1. Divida seus 5 anos de dados em 5 partes (1 ano cada)
2. Para cada threshold candidato (1.0, 1.25, 1.5, 1.75, 2.0):
   - Treine com 4 anos, teste em 1 ano
   - Repita 5 vezes, cada vez deixando 1 ano diferente de fora
   - Calcule a média de performance
3. Escolha o threshold que teve a melhor média **e** menor variação entre os testes

**Método 2: Penalizar Múltiplos Testes (Deflated Sharpe Ratio)**

Marcos López de Prado, um dos maiores especialistas em trading quantitativo, criou uma fórmula que "desconta" o Sharpe Ratio baseado em quantos testes você fez.

A ideia é simples: se você testar 100 estratégias, por pura sorte algumas terão Sharpe alto. O Deflated Sharpe Ratio calcula a probabilidade de que seu resultado seja genuíno, não sorte.

**Regra prática de López de Prado**:

| Anos de Dados | Máximo de Variações a Testar |
|---------------|------------------------------|
| 2 anos | 7 variações |
| 5 anos | 45 variações |
| 10 anos | 160 variações |

Com nossos ~5 anos de dados, devemos testar no máximo 20-30 combinações de parâmetros. Se testarmos 1000 variações, qualquer resultado bom é provavelmente sorte.

### Nosso Processo de Escolha de Threshold

1. **Definir candidatos a priori**: Antes de olhar qualquer resultado, definimos que vamos testar 1.0, 1.25, 1.5, 1.75, 2.0 (apenas 5 opções)
2. **Walk-forward em cada um**: Para cada threshold, rodamos o Walk-Forward completo
3. **Comparar estabilidade**: Escolhemos não o que teve maior retorno, mas o que teve retorno consistente em todos os períodos
4. **Calcular Deflated Sharpe**: Aplicamos a correção de López de Prado para verificar se o resultado é estatisticamente significativo
5. **Documentar tudo**: Registramos quantos testes fizemos, para que no futuro possamos saber se nossos resultados são confiáveis

### Por Que 1.5σ Pode Ser Razoável (Mas Precisa Validar)

O valor 1.5 desvios-padrão tem uma justificativa teórica:

- 1.0σ: ~32% dos dias terão movimentos maiores que isso → muitos sinais, muito ruído
- 1.5σ: ~13% dos dias → sinais moderados
- 2.0σ: ~5% dos dias → poucos sinais, podem perder oportunidades

Para nossa estratégia de holding de 1-5 dias, queremos sinais moderadamente raros. Mas isso é apenas teoria — precisamos validar com os dados.

---

## 5. Limitações do Teste de Granger: O Que Ele Não Conta

### O Que É o Teste de Granger?

O teste de Granger verifica se uma série temporal (minério) ajuda a prever outra (VALE3). A pergunta que ele responde é:

> "Saber o que aconteceu com o minério ontem me ajuda a prever VALE3 hoje, melhor do que apenas saber o que aconteceu com VALE3 ontem?"

Se a resposta for sim, dizemos que o minério "Granger-causa" a VALE3.

### O Que Granger NÃO Significa

**Granger-causa ≠ Causa de verdade**

Correlação (e Granger) não implica causalidade. Exemplos famosos:

- Vendas de sorvete e afogamentos estão correlacionados. Sorvete causa afogamento? Não. Ambos são causados pelo verão.
- O canto do galo precede o nascer do sol. O galo causa o sol? Não.

### Limitações Específicas Para Nossa Estratégia

**Limitação 1: Variável Oculta (Confounding)**

Pode existir um terceiro fator que causa ambos:

```
                    NOTÍCIAS DA CHINA
                    (demanda de aço)
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      MINÉRIO SGX                  VALE3
      (reage primeiro)        (reage depois)
```

Neste caso, minério não "causa" VALE3 — ambos reagem à mesma notícia. O minério reage primeiro porque o mercado asiático abre antes. Se o mercado brasileiro abrisse primeiro, a relação se inverteria.

**Implicação**: Nossa estratégia pode funcionar, mas não porque minério "prevê" VALE3, e sim porque capturamos a reação atrasada do mercado brasileiro às mesmas notícias.

**Limitação 2: Lag Fixo**

Granger assume que a relação tem um atraso fixo (ex: sempre 1 dia). Mas na realidade:

- Em dias calmos, a reação pode demorar 1 dia
- Em dias voláteis, a reação pode ser em horas
- Em crises, pode não haver relação

**Limitação 3: Linearidade**

Granger só captura relações lineares. Mas mercados podem ter relações não-lineares:

- Pequenos movimentos de minério → VALE3 ignora
- Grandes movimentos de minério → VALE3 reage proporcionalmente
- Movimentos extremos de minério → VALE3 entra em pânico e cai mais que o esperado

**Limitação 4: Instabilidade Temporal**

A relação pode existir em alguns períodos e desaparecer em outros:

- 2021: Correlação forte (China demandando muito)
- 2022: Correlação fraca (lockdowns na China, incerteza)
- 2023: Correlação média (recuperação)

Se você rodar Granger em todos os dados juntos, pode encontrar significância, mas isso mascara a instabilidade.

### Como Mitigamos Essas Limitações

| Limitação | Mitigação |
|-----------|-----------|
| Variável oculta | Aceitar que estamos capturando "reação atrasada", não causalidade. Isso ainda pode ser lucrativo. |
| Lag fixo | Testar múltiplos lags (1, 2, 3, 5 dias) e verificar qual é mais estável |
| Linearidade | Complementar Granger com Transfer Entropy (captura relações não-lineares) |
| Instabilidade | Rodar Granger em janelas rolling de 60 dias e verificar em quantas janelas a relação é significativa |

### Testes Complementares Que Usamos

| Teste | O Que Ele Faz | Quando Usar |
|-------|---------------|-------------|
| **Granger Causality** | Verifica se X ajuda a prever Y (linear) | Sempre — é o baseline |
| **Transfer Entropy** | Verifica transferência de informação (não-linear) | Para confirmar Granger |
| **Cointegração Johansen** | Verifica se X e Y têm relação de longo prazo | Para entender se há equilíbrio |
| **Rolling Granger** | Granger em janelas móveis | Para verificar estabilidade |

### Critério de Aprovação

Para considerarmos a relação minério→VALE3 válida:

1. Granger significativo (p < 0.05) em pelo menos 2 lags diferentes
2. Transfer Entropy minério→VALE3 maior que VALE3→minério
3. Rolling Granger significativo em pelo menos 60% das janelas de 60 dias
4. Relação não se inverte em nenhum subperíodo de 6+ meses

Se qualquer um desses falhar, devemos questionar seriamente a hipótese.

---

## 6. Reconciliação: Verificando Se Tudo Está Certo

### O Que É Reconciliação?

Reconciliação é comparar duas fontes de verdade para garantir que concordam. No nosso contexto:

- **Fonte 1**: O que nosso sistema acha que aconteceu (registros no Supabase)
- **Fonte 2**: O que realmente aconteceu (extrato da corretora Clear/MT5)

### Por Que É Crítico?

Bugs acontecem. Conexões caem. Ordens podem:

- Ser enviadas mas não executadas
- Ser executadas parcialmente
- Ser executadas a preço diferente do esperado
- Ser registradas no sistema mas rejeitadas pela corretora
- Ser executadas na corretora mas não registradas no sistema

Se não reconciliarmos, podemos achar que estamos lucrando enquanto estamos perdendo (ou vice-versa).

### O Que Reconciliamos

| Item | Sistema (Supabase) | Corretora (MT5/Clear) | O Que Verificar |
|------|-------------------|----------------------|-----------------|
| **Posições abertas** | Tabela `positions` | `mt5.positions_get()` | Quantidade, direção, preço médio |
| **Ordens do dia** | Tabela `orders` | `mt5.history_orders_get()` | Status, preço executado, horário |
| **Saldo** | Não armazenamos | `mt5.account_info()` | Comparar com expectativa |
| **P&L** | Calculado | Extrato da corretora | Deve bater exatamente |

### Tipos de Discrepância e Ações

| Discrepância | Gravidade | Ação |
|--------------|-----------|------|
| Posição existe no sistema mas não na corretora | **CRÍTICA** | Parar tudo, investigar imediatamente |
| Posição existe na corretora mas não no sistema | **CRÍTICA** | Parar tudo, pode ser posição "fantasma" |
| Quantidade diferente | **ALTA** | Pausar, corrigir registros |
| Preço médio difere < 0.5% | **BAIXA** | Registrar, monitorar |
| Preço médio difere > 0.5% | **MÉDIA** | Investigar slippage |
| Ordem pendente no sistema, executada na corretora | **ALTA** | Atualizar sistema, verificar alertas |

### Quando Reconciliar

| Momento | Tipo de Reconciliação |
|---------|----------------------|
| **Toda manhã (09:00)** | Posições: sistema vs corretora |
| **Após cada ordem** | Ordem específica: status, preço, quantidade |
| **Fim do dia (18:00)** | Completa: posições, ordens, P&L |
| **Fim de semana** | Auditoria: verificar últimos 5 dias em detalhe |

### Alertas de Reconciliação

Se encontrarmos discrepância:

1. **Alerta imediato via Telegram** com detalhes
2. **Pausar novas operações** até resolver
3. **Registrar no log** para auditoria
4. **Resolução manual** — nunca corrigir automaticamente discrepâncias críticas

### O Que Nunca Fazer

- Nunca ignorar discrepâncias pequenas — elas podem indicar bugs maiores
- Nunca corrigir automaticamente — humano deve validar
- Nunca operar sem reconciliação do dia anterior

---

## 7. Versionamento de Modelo: Histórico de Mudanças

### Por Que Versionar?

Imagine que sua estratégia está perdendo dinheiro. Você quer saber:

- Quando foi a última mudança?
- O que mudou?
- Como era a performance antes da mudança?
- Podemos voltar à versão anterior?

Sem versionamento, você está voando às cegas.

### O Que Versionamos

| Componente | O Que Guardar | Por Quê |
|------------|---------------|---------|
| **Parâmetros** | Threshold, janelas, limites | Para reproduzir exatamente o comportamento |
| **Código** | Versão do Git (commit hash) | Para saber qual lógica estava rodando |
| **Dados de treino** | Período usado, número de observações | Para entender o contexto |
| **Métricas** | Sharpe, win rate, max drawdown | Para comparar versões |
| **Decisão** | Por que mudamos | Para aprender com o histórico |

### Estrutura de Uma Versão

Cada "versão" do modelo deve ter um registro assim:

```
Versão: v1.2.0
Data: 2026-01-15
Commit Git: abc123def

Parâmetros:
- Threshold: 1.5σ
- Janela volatilidade: 20 dias
- Stop loss: 2x ATR(14)
- Correlação mínima: 0.2

Dados de Treino:
- Período: 2021-01-01 a 2024-06-30
- Observações: 875 dias
- Walk-forward folds: 8

Métricas (out-of-sample):
- Sharpe: 1.23
- Win rate: 54%
- Max drawdown: 8.7%
- Trades por mês: 3.2

Motivo da Mudança:
- Ajuste trimestral de threshold
- Threshold anterior (1.25σ) gerava muitos sinais fracos

Aprovado por: [seu nome]
```

### Quando Criar Nova Versão

| Evento | Nova Versão? | Tipo |
|--------|--------------|------|
| Ajuste trimestral de threshold | Sim | Minor (v1.1 → v1.2) |
| Correção de bug | Sim | Patch (v1.2.0 → v1.2.1) |
| Mudança de lógica de sinal | Sim | Major (v1.x → v2.0) |
| Novo período de treino (mensal) | Não | Apenas registro |
| Atualização de stop diário | Não | Operacional, não modelo |

### Regras de Versionamento

1. **Nunca sobrescrever**: Versões antigas devem ser preservadas para sempre
2. **Testar antes de promover**: Nova versão roda em paper trading antes de ir para produção
3. **Rollback fácil**: Deve ser possível voltar à versão anterior em minutos
4. **Documentar sempre**: Toda mudança precisa de justificativa escrita

### Comparação Entre Versões

Periodicamente, comparamos versões para entender evolução:

| Métrica | v1.0 | v1.1 | v1.2 | Tendência |
|---------|------|------|------|-----------|
| Sharpe | 1.10 | 1.18 | 1.23 | Melhorando |
| Win rate | 52% | 53% | 54% | Estável |
| Max DD | 10.2% | 9.1% | 8.7% | Melhorando |
| Trades/mês | 4.5 | 3.8 | 3.2 | Reduzindo |

Se uma versão nova tem métricas piores que a anterior, devemos investigar antes de usar em produção.

### Onde Guardamos as Versões

1. **Código**: Git (GitHub) — cada versão é um tag (v1.0.0, v1.1.0, etc.)
2. **Parâmetros**: Tabela `model_versions` no Supabase
3. **Métricas**: Tabela `model_performance` no Supabase
4. **Documentação**: Pasta `docs/versions/` com markdown de cada versão

---

## Resumo: Checklist de Validação

Antes de colocar qualquer versão em produção com dinheiro real:

### Checklist Estatístico

- [ ] Walk-forward com pelo menos 8 períodos out-of-sample
- [ ] Sharpe médio > 1.0 nos períodos de teste
- [ ] Sharpe positivo em > 70% dos períodos
- [ ] Granger significativo em 2+ lags
- [ ] Rolling Granger significativo em > 60% das janelas
- [ ] Deflated Sharpe Ratio > 50% (resultado não é sorte)
- [ ] Testamos menos de 30 variações de parâmetros

### Checklist Operacional

- [ ] Reconciliação do dia anterior sem discrepâncias
- [ ] Versão documentada com todos os parâmetros
- [ ] Código commitado e com tag no Git
- [ ] Paper trading de pelo menos 5 dias sem erros
- [ ] Kill switches testados e funcionando
- [ ] Alertas Telegram configurados

### Checklist de Regime

- [ ] Volatilidade atual < 1.5x da média histórica
- [ ] Correlação rolling > 0.2 nos últimos 20 dias
- [ ] Nenhum evento de crise detectado
- [ ] Mercado não está em período de feriado/baixa liquidez

---

## Glossário

| Termo | Definição Simples |
|-------|-------------------|
| **Backtest** | Testar uma estratégia em dados históricos |
| **Walk-Forward** | Backtest que simula o processo real de trading |
| **Overfitting** | Ajustar demais aos dados históricos, perdendo capacidade de generalizar |
| **Sharpe Ratio** | Retorno dividido pelo risco; quanto maior, melhor |
| **Granger Causality** | Teste se uma série ajuda a prever outra |
| **Transfer Entropy** | Versão mais sofisticada de Granger, captura relações não-lineares |
| **Regime** | "Estado" do mercado (alta, baixa, crise, etc.) |
| **Threshold** | Limite que define quando um movimento é significativo |
| **Desvio-padrão (σ)** | Medida de quanto os valores variam em torno da média |
| **Reconciliação** | Comparar duas fontes para garantir que concordam |
| **Versionamento** | Manter histórico de mudanças com possibilidade de voltar atrás |
| **Paper Trading** | Simular trading sem dinheiro real |
| **Kill Switch** | Botão de emergência para parar tudo |

---

## Referências

- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.
- López de Prado, M. & Bailey, D. (2014). *The Deflated Sharpe Ratio*. Journal of Portfolio Management.
- Chan, E. (2013). *Algorithmic Trading: Winning Strategies and Their Rationale*. Wiley.
- Bandy, H. (2007). *Quantitative Trading Systems*. Blue Owl Press.

---

*Documento criado em Janeiro 2026. Revisar trimestralmente.*
