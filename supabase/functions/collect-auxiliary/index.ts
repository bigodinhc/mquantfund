// Edge Function: Coleta dados auxiliares (USD/BRL, VIX, IBOV)
// Fontes: Yahoo Finance
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart";

// Símbolos auxiliares
const AUXILIARY_SYMBOLS = {
  USD_BRL: "BRL=X",      // USD/BRL
  VIX: "^VIX",           // CBOE Volatility Index
  IBOV: "^BVSP",         // Ibovespa
};

interface QuoteData {
  price: number;
  timestamp: number;
}

async function fetchYahooPrice(symbol: string): Promise<QuoteData | null> {
  try {
    const url = `${YAHOO_BASE_URL}/${symbol}?interval=1d&range=1d`;
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; QuantFund/1.0)",
      },
    });

    if (!response.ok) {
      console.error(`Yahoo API error for ${symbol}: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const meta = data.chart?.result?.[0]?.meta;

    if (!meta?.regularMarketPrice) {
      console.error(`No price data for ${symbol}`);
      return null;
    }

    return {
      price: meta.regularMarketPrice,
      timestamp: meta.regularMarketTime,
    };
  } catch (error) {
    console.error(`Error fetching ${symbol}: ${error}`);
    return null;
  }
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

    // Coletar todos os dados em paralelo
    const [usdBrl, vix, ibov] = await Promise.all([
      fetchYahooPrice(AUXILIARY_SYMBOLS.USD_BRL),
      fetchYahooPrice(AUXILIARY_SYMBOLS.VIX),
      fetchYahooPrice(AUXILIARY_SYMBOLS.IBOV),
    ]);

    // Usar o timestamp mais recente
    const timestamps = [usdBrl?.timestamp, vix?.timestamp, ibov?.timestamp].filter(Boolean);
    const latestTimestamp = Math.max(...(timestamps as number[]));
    const timestamp = new Date(latestTimestamp * 1000).toISOString();

    // Preparar dados
    const auxiliaryData = {
      timestamp,
      usd_brl: usdBrl?.price || null,
      vix: vix?.price || null,
      ibov: ibov?.price || null,
    };

    // Salvar no banco
    const { data, error } = await supabase
      .from("auxiliary_data")
      .upsert(auxiliaryData, {
        onConflict: "timestamp",
      })
      .select()
      .single();

    // Coletar erros
    const errors: string[] = [];
    if (!usdBrl) errors.push("USD/BRL: fetch failed");
    if (!vix) errors.push("VIX: fetch failed");
    if (!ibov) errors.push("IBOV: fetch failed");
    if (error) errors.push(`DB: ${error.message}`);

    // Log no sistema
    await supabase.from("system_logs").insert({
      level: errors.length > 0 ? "WARNING" : "INFO",
      component: "collect-auxiliary",
      message: `Collected auxiliary data: USD/BRL=${usdBrl?.price}, VIX=${vix?.price}, IBOV=${ibov?.price}`,
      details: { data: auxiliaryData, errors },
    });

    return new Response(
      JSON.stringify({
        success: error === null,
        data: {
          usd_brl: usdBrl?.price,
          vix: vix?.price,
          ibov: ibov?.price,
          timestamp,
        },
        errors: errors.length > 0 ? errors : undefined,
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
