// Edge Function: Coleta preços de minério de ferro
// Fontes: Yahoo Finance (SGX Iron Ore Futures)
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const YAHOO_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart";

// Símbolos de minério de ferro
const IRON_ORE_SYMBOLS = {
  // SGX Iron Ore 62% Fe CFR China Futures
  SGX_FE_62: "GC=F", // Usando Gold como proxy temporário - verificar ticker correto
};

interface YahooQuote {
  regularMarketPrice: number;
  regularMarketOpen: number;
  regularMarketHigh: number;
  regularMarketLow: number;
  regularMarketVolume: number;
  regularMarketTime: number;
}

async function fetchYahooQuote(symbol: string): Promise<YahooQuote | null> {
  try {
    const url = `${YAHOO_BASE_URL}/${symbol}?interval=1d&range=1d`;
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; QuantFund/1.0)",
      },
    });

    if (!response.ok) {
      console.error(`Yahoo API error: ${response.status}`);
      return null;
    }

    const data = await response.json();
    const result = data.chart?.result?.[0];

    if (!result?.meta) {
      console.error("No data in Yahoo response");
      return null;
    }

    const meta = result.meta;
    return {
      regularMarketPrice: meta.regularMarketPrice,
      regularMarketOpen: meta.previousClose || meta.regularMarketPrice,
      regularMarketHigh: meta.regularMarketDayHigh || meta.regularMarketPrice,
      regularMarketLow: meta.regularMarketDayLow || meta.regularMarketPrice,
      regularMarketVolume: meta.regularMarketVolume || 0,
      regularMarketTime: meta.regularMarketTime,
    };
  } catch (error) {
    console.error(`Error fetching Yahoo quote: ${error}`);
    return null;
  }
}

Deno.serve(async (req: Request) => {
  try {
    // Verificar método
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

    const results: Record<string, unknown> = {};
    const errors: string[] = [];

    // Coletar dados de cada símbolo
    for (const [name, symbol] of Object.entries(IRON_ORE_SYMBOLS)) {
      console.log(`Fetching ${name} (${symbol})...`);

      const quote = await fetchYahooQuote(symbol);

      if (quote) {
        const timestamp = new Date(quote.regularMarketTime * 1000).toISOString();

        const { data, error } = await supabase
          .from("prices_iron_ore")
          .upsert({
            timestamp,
            source: "yahoo",
            symbol: name,
            price: quote.regularMarketPrice,
            open: quote.regularMarketOpen,
            high: quote.regularMarketHigh,
            low: quote.regularMarketLow,
            close: quote.regularMarketPrice,
            volume: quote.regularMarketVolume,
          }, {
            onConflict: "timestamp,source,symbol",
          })
          .select()
          .single();

        if (error) {
          errors.push(`${name}: ${error.message}`);
        } else {
          results[name] = {
            price: quote.regularMarketPrice,
            timestamp,
            saved: true,
          };
        }
      } else {
        errors.push(`${name}: Failed to fetch quote`);
      }
    }

    // Log no sistema
    await supabase.from("system_logs").insert({
      level: errors.length > 0 ? "WARNING" : "INFO",
      component: "collect-iron-ore",
      message: `Collected ${Object.keys(results).length} prices, ${errors.length} errors`,
      details: { results, errors },
    });

    return new Response(
      JSON.stringify({
        success: errors.length === 0,
        collected: Object.keys(results).length,
        results,
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
