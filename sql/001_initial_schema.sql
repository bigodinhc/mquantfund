-- ===========================================
-- QUANTFUND - Schema Inicial para Supabase
-- ===========================================
-- Execute este script no SQL Editor do Supabase
-- Dashboard > SQL Editor > New Query

-- -------------------------------------------
-- Tabela: prices_iron_ore
-- Preços de minério de ferro (SGX, DCE)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS prices_iron_ore (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'yahoo', 'investing', 'sgx', 'dce'
    symbol VARCHAR(50) NOT NULL,  -- 'SGX_FE_62', 'DCE_IO'
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(timestamp, source, symbol)
);

-- Índice para consultas por tempo
CREATE INDEX IF NOT EXISTS idx_iron_ore_timestamp ON prices_iron_ore(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_iron_ore_source ON prices_iron_ore(source, timestamp DESC);

-- -------------------------------------------
-- Tabela: prices_vale3
-- Preços de VALE3 (B3 via MT5)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS prices_vale3 (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'mt5',  -- 'mt5', 'cedro', 'yahoo'
    symbol VARCHAR(20) NOT NULL DEFAULT 'VALE3',
    open DECIMAL(10, 2) NOT NULL,
    high DECIMAL(10, 2) NOT NULL,
    low DECIMAL(10, 2) NOT NULL,
    close DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    tick_volume BIGINT,
    spread INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(timestamp, source, symbol)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_vale3_timestamp ON prices_vale3(timestamp DESC);

-- -------------------------------------------
-- Tabela: auxiliary_data
-- Dados auxiliares (USD/BRL, VIX)
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS auxiliary_data (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    usd_brl DECIMAL(10, 4),
    vix DECIMAL(10, 2),
    ibov DECIMAL(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(timestamp)
);

CREATE INDEX IF NOT EXISTS idx_auxiliary_timestamp ON auxiliary_data(timestamp DESC);

-- -------------------------------------------
-- Tabela: signals
-- Sinais gerados pelo sistema
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    signal_type VARCHAR(20) NOT NULL,  -- 'LONG', 'SHORT', 'NEUTRAL', 'EXIT'
    symbol VARCHAR(20) NOT NULL DEFAULT 'VALE3',
    confidence DECIMAL(5, 4),  -- 0.0000 a 1.0000
    iron_ore_return DECIMAL(10, 6),
    iron_ore_zscore DECIMAL(10, 4),
    features_json JSONB,  -- Todas as features usadas
    strategy VARCHAR(50),  -- 'rule_based', 'ml_xgboost', 'hybrid'
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_executed ON signals(executed, timestamp DESC);

-- -------------------------------------------
-- Tabela: orders
-- Ordens enviadas e executadas
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    order_id_internal VARCHAR(50) NOT NULL,  -- ID interno do sistema
    order_id_exchange VARCHAR(50),  -- ID da corretora/exchange
    signal_id BIGINT REFERENCES signals(id),
    symbol VARCHAR(20) NOT NULL DEFAULT 'VALE3',
    side VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL'
    order_type VARCHAR(20) NOT NULL,  -- 'MARKET', 'LIMIT', 'STOP'
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2),  -- Preço limite (se aplicável)
    stop_price DECIMAL(10, 2),  -- Preço stop (se aplicável)
    status VARCHAR(20) NOT NULL,  -- 'PENDING', 'SENT', 'FILLED', 'PARTIAL', 'CANCELLED', 'REJECTED'
    fill_price DECIMAL(10, 2),
    fill_quantity INTEGER,
    slippage_bps DECIMAL(10, 2),  -- Slippage em basis points
    commission DECIMAL(10, 4),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orders_internal_id ON orders(order_id_internal);

-- -------------------------------------------
-- Tabela: positions
-- Posições abertas
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL DEFAULT 'VALE3',
    side VARCHAR(10) NOT NULL,  -- 'LONG', 'SHORT'
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10, 2) NOT NULL,
    entry_timestamp TIMESTAMPTZ NOT NULL,
    current_price DECIMAL(10, 2),
    unrealized_pnl DECIMAL(12, 2),
    stop_loss DECIMAL(10, 2),
    take_profit DECIMAL(10, 2),
    trailing_stop DECIMAL(10, 2),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',  -- 'OPEN', 'CLOSED'
    exit_price DECIMAL(10, 2),
    exit_timestamp TIMESTAMPTZ,
    realized_pnl DECIMAL(12, 2),
    exit_reason VARCHAR(50),  -- 'STOP_LOSS', 'TAKE_PROFIT', 'TRAILING', 'SIGNAL', 'MANUAL', 'TIME_STOP'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol, status);

-- -------------------------------------------
-- Tabela: daily_metrics
-- Métricas diárias consolidadas
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS daily_metrics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    starting_capital DECIMAL(12, 2),
    ending_capital DECIMAL(12, 2),
    daily_pnl DECIMAL(12, 2),
    daily_return DECIMAL(10, 6),
    trades_count INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    max_drawdown DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 4),
    correlation_iron_vale DECIMAL(10, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC);

-- -------------------------------------------
-- Tabela: system_logs
-- Logs do sistema para auditoria
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS system_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component VARCHAR(50),  -- 'data_fetcher', 'signal_generator', 'executor', etc.
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level, timestamp DESC);

-- -------------------------------------------
-- Tabela: kill_switch_events
-- Registro de eventos de kill switch
-- -------------------------------------------
CREATE TABLE IF NOT EXISTS kill_switch_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level INTEGER NOT NULL,  -- 1, 2, 3, 4
    trigger_reason VARCHAR(100) NOT NULL,
    action_taken TEXT NOT NULL,
    positions_closed INTEGER DEFAULT 0,
    pnl_at_trigger DECIMAL(12, 2),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_killswitch_timestamp ON kill_switch_events(timestamp DESC);

-- -------------------------------------------
-- Views úteis
-- -------------------------------------------

-- View: Última posição aberta
CREATE OR REPLACE VIEW v_open_positions AS
SELECT * FROM positions WHERE status = 'OPEN';

-- View: P&L do dia
CREATE OR REPLACE VIEW v_today_pnl AS
SELECT
    COALESCE(SUM(realized_pnl), 0) as realized_pnl,
    COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl,
    COUNT(*) FILTER (WHERE status = 'CLOSED' AND exit_timestamp::date = CURRENT_DATE) as trades_today
FROM positions
WHERE entry_timestamp::date = CURRENT_DATE OR (status = 'OPEN');

-- View: Últimos sinais
CREATE OR REPLACE VIEW v_recent_signals AS
SELECT * FROM signals
ORDER BY timestamp DESC
LIMIT 50;

-- -------------------------------------------
-- Comentários nas tabelas
-- -------------------------------------------
COMMENT ON TABLE prices_iron_ore IS 'Preços históricos de minério de ferro (SGX, DCE)';
COMMENT ON TABLE prices_vale3 IS 'Preços históricos de VALE3 via MT5';
COMMENT ON TABLE auxiliary_data IS 'Dados auxiliares: USD/BRL, VIX, IBOV';
COMMENT ON TABLE signals IS 'Sinais de trading gerados pelo sistema';
COMMENT ON TABLE orders IS 'Ordens enviadas para execução';
COMMENT ON TABLE positions IS 'Posições abertas e histórico';
COMMENT ON TABLE daily_metrics IS 'Métricas diárias consolidadas';
COMMENT ON TABLE system_logs IS 'Logs do sistema para auditoria';
COMMENT ON TABLE kill_switch_events IS 'Registro de eventos de kill switch';

-- -------------------------------------------
-- Grants (Row Level Security - opcional)
-- -------------------------------------------
-- Se quiser habilitar RLS, descomente:
-- ALTER TABLE prices_iron_ore ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE prices_vale3 ENABLE ROW LEVEL SECURITY;
-- etc.

-- ===========================================
-- FIM DO SCHEMA
-- ===========================================
