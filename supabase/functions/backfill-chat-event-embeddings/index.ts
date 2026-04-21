import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const EMBEDDING_MODEL = "text-embedding-3-small";
const EMBEDDING_DIMENSIONS = 512;

type DocumentRow = {
  event_id: number;
  content: string;
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

async function generateEmbeddings(inputs: string[]) {
  const openAiKey = Deno.env.get("OPENAI_API_KEY");
  if (!openAiKey) {
    throw new Error("OPENAI_API_KEY not configured");
  }

  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${openAiKey}`,
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: inputs,
      dimensions: EMBEDDING_DIMENSIONS,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("OpenAI embeddings error:", errorText);
    throw new Error(`OpenAI embeddings error: ${response.status}`);
  }

  const json = await response.json();
  const data = Array.isArray(json.data) ? json.data : [];
  return data.map((item: { embedding: number[] }) => item.embedding);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  const startedAt = Date.now();

  try {
    const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};
    const city = typeof body.city === "string" && body.city.trim()
      ? body.city.trim().toLowerCase()
      : "bloomington";
    const batchSize = typeof body.batch_size === "number" && Number.isFinite(body.batch_size)
      ? Math.max(1, Math.min(100, Math.trunc(body.batch_size)))
      : 25;

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error("Supabase service credentials are not configured");
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey);

    const { data: rows, error: selectError } = await supabase
      .from("chat_event_documents")
      .select("event_id, content")
      .eq("city", city)
      .is("embedding", null)
      .order("start_time", { ascending: true })
      .limit(batchSize);

    if (selectError) {
      throw selectError;
    }

    const documents = ((rows || []) as DocumentRow[]).filter((row) => typeof row.content === "string" && row.content.trim());
    if (!documents.length) {
      const { count: remaining } = await supabase
        .from("chat_event_documents")
        .select("*", { count: "exact", head: true })
        .eq("city", city)
        .is("embedding", null);

      return jsonResponse({
        city,
        processed: 0,
        remaining_null_embeddings: remaining ?? 0,
        elapsed_ms: Date.now() - startedAt,
      });
    }

    const embeddings = await generateEmbeddings(documents.map((row) => row.content));

    for (let i = 0; i < documents.length; i += 1) {
      const row = documents[i];
      const embedding = embeddings[i];
      if (!embedding) {
        continue;
      }
      const { error: updateError } = await supabase
        .from("chat_event_documents")
        .update({ embedding })
        .eq("event_id", row.event_id);
      if (updateError) {
        throw updateError;
      }
    }

    const { count: remaining } = await supabase
      .from("chat_event_documents")
      .select("*", { count: "exact", head: true })
      .eq("city", city)
      .is("embedding", null);

    return jsonResponse({
      city,
      processed: documents.length,
      remaining_null_embeddings: remaining ?? 0,
      elapsed_ms: Date.now() - startedAt,
      sample_event_ids: documents.slice(0, 5).map((row) => row.event_id),
      embedding_model: EMBEDDING_MODEL,
      embedding_dimensions: EMBEDDING_DIMENSIONS,
    });
  } catch (error) {
    console.error("backfill-chat-event-embeddings error:", error);
    return jsonResponse({ error: errorMessage(error) }, 500);
  }
});
