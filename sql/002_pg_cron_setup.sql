-- ===========================================
-- QUANTFUND - Setup pg_cron para agendamento
-- ===========================================
-- Execute no SQL Editor do Supabase após habilitar pg_cron
-- Dashboard > Database > Extensions > pg_cron

-- Habilitar extensão pg_cron (se não estiver habilitada)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Dar permissão para o schema cron
GRANT USAGE ON SCHEMA cron TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO postgres;

-- -------------------------------------------
-- Função auxiliar para chamar Edge Functions
-- -------------------------------------------
CREATE OR REPLACE FUNCTION call_edge_function(function_name TEXT)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    project_url TEXT;
    service_key TEXT;
    response_status INT;
BEGIN
    -- Pegar URL e key das variáveis de ambiente
    -- Nota: Em produção, use vault secrets
    project_url := current_setting('app.settings.supabase_url', true);
    service_key := current_setting('app.settings.supabase_service_role_key', true);

    -- Se não tiver configurado, usar fallback
    IF project_url IS NULL THEN
        project_url := 'https://chhcuivssqrkimwocera.supabase.co';
    END IF;

    -- Log da tentativa
    INSERT INTO system_logs (level, component, message, details)
    VALUES ('DEBUG', 'pg_cron', 'Calling edge function: ' || function_name,
            jsonb_build_object('function', function_name, 'timestamp', NOW()));

    -- A chamada real seria via pg_net (outra extensão)
    -- Por enquanto, apenas logamos
    -- Em produção: SELECT net.http_post(...)

END;
$$;

-- -------------------------------------------
-- Jobs de Coleta de Dados
-- -------------------------------------------

-- Coletar preços de minério a cada 5 minutos durante horário de mercado
-- SGX: 23:25(D-1) - 12:00 UTC
-- DCE: 01:00 - 07:00 UTC
SELECT cron.schedule(
    'collect-iron-ore-sgx',
    '*/5 0-12 * * 1-5',  -- A cada 5 min, 00:00-12:00 UTC, seg-sex
    $$
    INSERT INTO system_logs (level, component, message)
    VALUES ('INFO', 'pg_cron', 'Trigger: collect-iron-ore (SGX hours)');
    -- Em produção: SELECT net.http_post('https://chhcuivssqrkimwocera.supabase.co/functions/v1/collect-iron-ore', ...);
    $$
);

-- Coletar dados auxiliares a cada hora
SELECT cron.schedule(
    'collect-auxiliary-hourly',
    '0 * * * *',  -- A cada hora cheia
    $$
    INSERT INTO system_logs (level, component, message)
    VALUES ('INFO', 'pg_cron', 'Trigger: collect-auxiliary');
    $$
);

-- Verificar sinais na janela crítica (12:00-13:00 UTC)
SELECT cron.schedule(
    'check-signals-critical',
    '*/1 12 * * 1-5',  -- A cada minuto das 12:00-12:59 UTC, seg-sex
    $$
    INSERT INTO system_logs (level, component, message)
    VALUES ('INFO', 'pg_cron', 'Trigger: check-signals (critical window)');
    $$
);

-- Verificar sinal às 13:00 UTC (abertura B3)
SELECT cron.schedule(
    'check-signals-b3-open',
    '0 13 * * 1-5',  -- 13:00 UTC, seg-sex
    $$
    INSERT INTO system_logs (level, component, message)
    VALUES ('INFO', 'pg_cron', 'Trigger: check-signals (B3 open)');
    $$
);

-- -------------------------------------------
-- Jobs de Manutenção
-- -------------------------------------------

-- Limpar logs antigos (manter 30 dias)
SELECT cron.schedule(
    'cleanup-old-logs',
    '0 3 * * *',  -- 03:00 UTC diariamente
    $$
    DELETE FROM system_logs
    WHERE created_at < NOW() - INTERVAL '30 days';
    $$
);

-- -------------------------------------------
-- View para ver jobs agendados
-- -------------------------------------------
CREATE OR REPLACE VIEW v_cron_jobs AS
SELECT
    jobid,
    schedule,
    command,
    nodename,
    nodeport,
    database,
    username,
    active
FROM cron.job
ORDER BY jobid;

-- -------------------------------------------
-- Comentários
-- -------------------------------------------
COMMENT ON FUNCTION call_edge_function IS 'Função auxiliar para chamar Edge Functions via pg_cron';

-- ===========================================
-- NOTA IMPORTANTE
-- ===========================================
-- Para chamar Edge Functions de verdade, você precisa:
-- 1. Habilitar a extensão pg_net no Supabase
-- 2. Usar net.http_post() para fazer requisições HTTP
--
-- Exemplo:
-- SELECT net.http_post(
--     url := 'https://chhcuivssqrkimwocera.supabase.co/functions/v1/collect-iron-ore',
--     headers := jsonb_build_object(
--         'Content-Type', 'application/json',
--         'Authorization', 'Bearer ' || current_setting('app.settings.supabase_service_role_key')
--     ),
--     body := '{}'::jsonb
-- );
-- ===========================================
