// Edge Function: Verifica sinais de trading na janela crítica
// Executa durante a janela SGX close -> B3 open (12:00-13:00 UTC)
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Parâmetros da estratégia
const STRATEGY_PARAMS = {
  SIGNAL_THRESHOLD_STD: 1.5,  // Desvios padrão para sinal
  ROLLING_WINDOW: 20,         // Dias para cálculo de volatilidade
  MIN_CONFIDENCE: 0.6,        // Confiança mínima para gerar sinal
};

interface PriceData {
  timestamp: string;
  price: number;
  close: number;
}

interface SignalResult {
  signal_type: "LONG" | "SHORT" | "NEUTRAL";
  confidence: number;
  iron_ore_return: number;
  iron_ore_zscore: number;
}

function calculateZScore(values: number[], current: number): number {
  if (values.length < 2) return 0;

  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const std = Math.sqrt(variance);

  if (std === 0) return 0;
  return (current - mean) / std;
}

function calculateReturns(prices: number[]): number[] {
  const returns: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
  }
  return returns;
}

async function generateSignal(supabase: ReturnType<typeof createClient>): Promise<SignalResult> {
  // Buscar últimos N dias de preços de minério
  const { data: ironOrePrices, error: ironError } = await supabase
    .from("prices_iron_ore")
    .select("timestamp, price, close")
    .order("timestamp", { ascending: false })
    .limit(STRATEGY_PARAMS.ROLLING_WINDOW + 1);

  if (ironError || !ironOrePrices || ironOrePrices.length < 5) {
    console.log("Insufficient iron ore data");
    return {
      signal_type: "NEUTRAL",
      confidence: 0,
      iron_ore_return: 0,
      iron_ore_zscore: 0,
    };
  }

  // Calcular retornos
  const prices = ironOrePrices
    .map((p) => p.close || p.price)
    .reverse(); // Ordenar do mais antigo pro mais recente

  const returns = calculateReturns(prices);

  if (returns.length < 2) {
    return {
      signal_type: "NEUTRAL",
      confidence: 0,
      iron_ore_return: 0,
      iron_ore_zscore: 0,
    };
  }

  // Último retorno e z-score
  const currentReturn = returns[returns.length - 1];
  const historicalReturns = returns.slice(0, -1);
  const zscore = calculateZScore(historicalReturns, currentReturn);

  // Gerar sinal baseado no z-score
  let signal_type: "LONG" | "SHORT" | "NEUTRAL" = "NEUTRAL";
  let confidence = 0;

  if (zscore > STRATEGY_PARAMS.SIGNAL_THRESHOLD_STD) {
    // Minério subiu muito -> VALE3 deve subir -> LONG
    signal_type = "LONG";
    confidence = Math.min(0.95, 0.5 + (zscore - STRATEGY_PARAMS.SIGNAL_THRESHOLD_STD) * 0.15);
  } else if (zscore < -STRATEGY_PARAMS.SIGNAL_THRESHOLD_STD) {
    // Minério caiu muito -> VALE3 deve cair -> SHORT (ou não operar)
    signal_type = "SHORT";
    confidence = Math.min(0.95, 0.5 + (Math.abs(zscore) - STRATEGY_PARAMS.SIGNAL_THRESHOLD_STD) * 0.15);
  } else {
    signal_type = "NEUTRAL";
    confidence = 0.5 - Math.abs(zscore) * 0.1;
  }

  return {
    signal_type,
    confidence: Math.max(0, Math.min(1, confidence)),
    iron_ore_return: currentReturn,
    iron_ore_zscore: zscore,
  };
}

Deno.serve(async (req: Request) => {
  try {
    // CORS preflight
    if (req.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Criar cliente Supabase
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Verificar se estamos na janela crítica (12:00-13:00 UTC)
    const now = new Date();
    const utcHour = now.getUTCHours();
    const utcMinute = now.getUTCMinutes();

    const inCriticalWindow = utcHour === 12 || (utcHour === 13 && utcMinute === 0);

    // Parâmetro para forçar execução (útil para testes)
    const url = new URL(req.url);
    const force = url.searchParams.get("force") === "true";

    if (!inCriticalWindow && !force) {
      return new Response(
        JSON.stringify({
          success: true,
          message: "Outside critical window (12:00-13:00 UTC)",
          current_time_utc: now.toISOString(),
          signal_generated: false,
        }),
        {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }

    // Gerar sinal
    const signal = await generateSignal(supabase);
    const timestamp = now.toISOString();

    // Só salvar se tiver confiança mínima ou for sinal acionável
    const shouldSave = signal.confidence >= STRATEGY_PARAMS.MIN_CONFIDENCE ||
                       signal.signal_type !== "NEUTRAL";

    let savedSignal = null;
    if (shouldSave) {
      const { data, error } = await supabase
        .from("signals")
        .insert({
          timestamp,
          signal_type: signal.signal_type,
          symbol: "VALE3",
          confidence: signal.confidence,
          iron_ore_return: signal.iron_ore_return,
          iron_ore_zscore: signal.iron_ore_zscore,
          strategy: "rule_based",
          features_json: {
            rolling_window: STRATEGY_PARAMS.ROLLING_WINDOW,
            threshold_std: STRATEGY_PARAMS.SIGNAL_THRESHOLD_STD,
            in_critical_window: inCriticalWindow,
            forced: force,
          },
          executed: false,
        })
        .select()
        .single();

      if (error) {
        console.error("Error saving signal:", error);
      } else {
        savedSignal = data;
      }
    }

    // Log no sistema
    await supabase.from("system_logs").insert({
      level: signal.signal_type !== "NEUTRAL" ? "INFO" : "DEBUG",
      component: "check-signals",
      message: `Signal generated: ${signal.signal_type} (confidence=${signal.confidence.toFixed(2)}, zscore=${signal.iron_ore_zscore.toFixed(2)})`,
      details: { signal, saved: shouldSave, forced: force },
    });

    return new Response(
      JSON.stringify({
        success: true,
        signal_generated: true,
        signal: {
          type: signal.signal_type,
          confidence: signal.confidence,
          iron_ore_return: signal.iron_ore_return,
          iron_ore_zscore: signal.iron_ore_zscore,
        },
        saved: shouldSave,
        saved_id: savedSignal?.id,
        timestamp,
        in_critical_window: inCriticalWindow,
      }),
      {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  } catch (error) {
    console.error("Function error:", error);
    return new Response(
      JSON.stringify({ success: false, error: String(error) }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
});
