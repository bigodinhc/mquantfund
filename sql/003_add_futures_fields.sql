-- ===========================================
-- QUANTFUND - Adiciona campos para contratos futuros
-- ===========================================
-- Adiciona variable_key, expiry_date e price_type para suportar
-- a cadeia completa de 12 meses de contratos de minério de ferro.

-- Adicionar campos
ALTER TABLE prices_iron_ore
ADD COLUMN IF NOT EXISTS variable_key VARCHAR(50),
ADD COLUMN IF NOT EXISTS expiry_date DATE,
ADD COLUMN IF NOT EXISTS price_type VARCHAR(20) DEFAULT 'intraday';

-- Comentários
COMMENT ON COLUMN prices_iron_ore.variable_key IS 'Identificador do contrato no formato DERIV_IO_SWAP_YYYY_MM';
COMMENT ON COLUMN prices_iron_ore.expiry_date IS 'Data de vencimento do contrato futuro';
COMMENT ON COLUMN prices_iron_ore.price_type IS 'Tipo do preço: intraday, settlement, close';

-- Índice para busca por variable_key (mais eficiente para análise de curva forward)
CREATE INDEX IF NOT EXISTS idx_iron_ore_variable_key
ON prices_iron_ore(variable_key, timestamp DESC);

-- Índice para busca por expiry_date
CREATE INDEX IF NOT EXISTS idx_iron_ore_expiry_date
ON prices_iron_ore(expiry_date, timestamp DESC);

-- Atualizar constraint de upsert (drop and recreate)
-- Primeiro, remover a constraint antiga se existir
ALTER TABLE prices_iron_ore
DROP CONSTRAINT IF EXISTS prices_iron_ore_timestamp_source_symbol_key;

-- Criar nova constraint incluindo variable_key
ALTER TABLE prices_iron_ore
ADD CONSTRAINT prices_iron_ore_timestamp_source_variable_key_key
UNIQUE (timestamp, source, variable_key);

-- ===========================================
-- NOTA: Após aplicar esta migração, os registros antigos
-- terão variable_key NULL. Você pode atualizar com:
--
-- UPDATE prices_iron_ore
-- SET variable_key = 'DERIV_IO_SWAP_' ||
--     EXTRACT(YEAR FROM expiry_date)::TEXT || '_' ||
--     LPAD(EXTRACT(MONTH FROM expiry_date)::TEXT, 2, '0')
-- WHERE variable_key IS NULL AND expiry_date IS NOT NULL;
-- ===========================================
