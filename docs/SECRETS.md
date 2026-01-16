# Configuração de Secrets - QuantFund

Este documento descreve como configurar os secrets necessários para o funcionamento do sistema.

## Secrets do GitHub Actions

### Como Configurar

1. Acesse seu repositório no GitHub
2. Vá em **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione cada secret conforme a tabela abaixo

### Fase 1: Validação Estatística (Obrigatórios)

| Secret | Descrição | Onde Obter |
|--------|-----------|------------|
| `SUPABASE_URL` | URL do projeto Supabase | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_SERVICE_KEY` | Service Role Key (backend) | Supabase Dashboard → Settings → API → service_role |

### Fase 2: Operação (Após GO)

| Secret | Descrição | Onde Obter |
|--------|-----------|------------|
| `LSEG_APP_KEY` | App Key do LSEG Workspace | Portal LSEG → App Management |
| `LSEG_USERNAME` | Usuário do LSEG | Credenciais da licença |
| `LSEG_PASSWORD` | Senha do LSEG | Credenciais da licença |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram | @BotFather no Telegram |
| `TELEGRAM_CHAT_ID` | ID do chat para notificações | Ver seção abaixo |

---

## Configuração Detalhada

### Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Entre no seu projeto
3. Vá em **Settings** → **API**
4. Copie:
   - **Project URL** → `SUPABASE_URL`
   - **service_role** (em Project API keys) → `SUPABASE_SERVICE_KEY`

> ⚠️ **Importante**: Use a `service_role` key apenas no backend/GitHub Actions. Nunca exponha no frontend.

### LSEG Workspace (Fase 2)

Se você tem acesso ao LSEG Workspace:

1. Acesse o portal de desenvolvedor LSEG
2. Crie uma aplicação
3. Obtenha:
   - **App Key** → `LSEG_APP_KEY`
   - Credenciais de login → `LSEG_USERNAME`, `LSEG_PASSWORD`

> 📝 **Nota**: Se não tiver LSEG, o sistema usará yfinance como fallback.

### Telegram Bot

#### Criando o Bot

1. Abra o Telegram e busque **@BotFather**
2. Envie `/newbot`
3. Escolha um nome (ex: "QuantFund Alerts")
4. Escolha um username (ex: "quantfund_alerts_bot")
5. Copie o token → `TELEGRAM_BOT_TOKEN`

#### Obtendo o Chat ID

1. Envie qualquer mensagem para seu bot
2. Acesse: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Procure por `"chat":{"id":NUMERO}` → `TELEGRAM_CHAT_ID`

---

## Verificação

### Testando Localmente

```bash
# Copie .env.example para .env e preencha os valores
cp .env.example .env

# Teste conexão Supabase
python -c "from src.db.client import test_connection; test_connection()"

# Teste Telegram (opcional)
python -m src.notifications.telegram_bot --test
```

### Testando no GitHub Actions

1. Vá em **Actions** → **Daily Tasks**
2. Clique em **Run workflow**
3. Selecione "backfill" e execute
4. Verifique os logs

---

## Troubleshooting

### Erro: "SUPABASE_URL não configurado"
- Verifique se o secret foi adicionado corretamente
- Confirme que não há espaços extras no valor

### Erro: "Invalid API key"
- Verifique se copiou a key completa (JWT)
- Confirme que está usando `service_role`, não `anon`

### Erro: "Telegram: Unauthorized"
- Verifique se o token está correto
- Confirme que o bot não foi bloqueado

### Workflow não executa no horário
- GitHub Actions usa UTC
- 06:00 UTC = 03:00 BRT
- Verifique se o repositório está ativo (commits recentes)

---

## Segurança

- ✅ **NUNCA** commite credenciais no código
- ✅ Use sempre GitHub Secrets para produção
- ✅ Rotacione secrets periodicamente
- ✅ Use `service_role` apenas no backend
- ❌ Não compartilhe o arquivo `.env`
- ❌ Não exponha secrets em logs

---

## Referência Rápida

```
Fase 1 (Mínimo):
├── SUPABASE_URL
└── SUPABASE_SERVICE_KEY

Fase 2 (Completo):
├── SUPABASE_URL
├── SUPABASE_SERVICE_KEY
├── LSEG_APP_KEY
├── LSEG_USERNAME
├── LSEG_PASSWORD
├── TELEGRAM_BOT_TOKEN
└── TELEGRAM_CHAT_ID
```
