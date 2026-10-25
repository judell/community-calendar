import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-ue-client-tx-id",
};

const RETRIEVAL_MODEL = "claude-haiku-4-5-20251001";
const REPLY_MODEL = "claude-haiku-4-5-20251001";
const EMBEDDING_MODEL = "text-embedding-3-small";
const EMBEDDING_DIMENSIONS = 512;
const CHAT_BETA_CITY = "bloomington";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type EventRow = {
  id: number;
  title: string;
  start_time: string;
  end_time: string | null;
  url: string | null;
  location: string | null;
  description: string | null;
  source: string | null;
  source_urls: Record<string, string> | null;
  category: string | null;
  image_url: string | null;
  all_day: boolean | null;
  city: string;
  merged_ids: number[] | null;
  rrf_score?: number | null;
  full_text_rank?: number | null;
  semantic_rank?: number | null;
};

type RetrievalPlan = {
  search_query: string;
  start_time?: string;
  end_time?: string;
  notes?: string;
};

type ChatBetaLogInsert = {
  user_id: string;
  city: string;
  latest_user_text: string;
  request_messages: ChatMessage[];
  intent_plan: Record<string, unknown> | null;
  planner_model: string;
  reply_model: string;
  planner_raw?: string | null;
  planner_error?: string | null;
  executed_sql: string;
  query_error?: string | null;
  used_fallback: boolean;
  planner_fallback_used: boolean;
  query_fallback_used: boolean;
  candidate_ids: number[];
  recommended_ids: number[];
  reply_text: string;
  reply_raw?: string | null;
  reply_error?: string | null;
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

function sanitizeConversationMessages(rawMessages: unknown[]): ChatMessage[] {
  return rawMessages.flatMap((item) => {
    if (!item || typeof item !== "object") {
      return [];
    }
    const record = item as Record<string, unknown>;
    const role = record.role;
    const content = record.content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string" || !content.trim()) {
      return [];
    }
    return [{ role, content: content.trim() } as ChatMessage];
  });
}

function parseJsonObject(rawText: string) {
  const text = rawText.trim();
  const unfenced = text.startsWith("```")
    ? text.replace(/^```(?:json)?\n?/, "").replace(/\n?```$/, "")
    : text;

  try {
    return JSON.parse(unfenced);
  } catch {
    const match = unfenced.match(/\{[\s\S]*\}/);
    if (match) {
      return JSON.parse(match[0]);
    }
    throw new Error("Model did not return valid JSON");
  }
}

function getLatestUserText(messages: ChatMessage[]) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === "user" && typeof messages[i].content === "string") {
      return messages[i].content;
    }
  }
  return "";
}

function summarizeEvents(events: EventRow[]) {
  return events.map((event) => ({
    id: event.id,
    title: event.title,
    start_time: event.start_time,
    end_time: event.end_time,
    location: event.location,
    category: event.category,
    source: event.source,
    description: event.description,
    url: event.url,
    rrf_score: event.rrf_score,
    full_text_rank: event.full_text_rank,
    semantic_rank: event.semantic_rank,
  }));
}

async function callAnthropic(system: string, messages: ChatMessage[], model: string, maxTokens = 1024) {
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!anthropicKey) {
    throw new Error("ANTHROPIC_API_KEY not configured");
  }

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": anthropicKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      system,
      messages,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("Anthropic API error:", errorText);
    throw new Error(`Anthropic API error: ${response.status}`);
  }

  const result = await response.json();
  return result.content?.find((item: any) => item.type === "text")?.text || "";
}

async function generateQueryEmbedding(query: string) {
  const openAiKey = Deno.env.get("OPENAI_API_KEY");
  if (!openAiKey || !query.trim()) {
    return null;
  }

  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${openAiKey}`,
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: query,
      dimensions: EMBEDDING_DIMENSIONS,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error("OpenAI embeddings error:", errorText);
    return null;
  }

  const json = await response.json();
  return json.data?.[0]?.embedding || null;
}

async function getAuthorizedBetaUserId(req: Request, supabase: ReturnType<typeof createClient>, city: string) {
  if (city !== CHAT_BETA_CITY) {
    throw new Error(`chat beta is currently limited to ${CHAT_BETA_CITY}`);
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) {
    return { userId: null, status: 401, error: "Sign in is required for concierge beta access." };
  }

  const token = authHeader.slice("Bearer ".length);
  const { data: userData, error: authError } = await supabase.auth.getUser(token);
  if (authError || !userData?.user?.id) {
    return { userId: null, status: 401, error: "Invalid authorization." };
  }

  const userId = userData.user.id;
  const { data: betaRow, error: betaError } = await supabase
    .from("chat_beta_users")
    .select("user_id")
    .eq("user_id", userId)
    .eq("city", city)
    .limit(1)
    .maybeSingle();

  if (betaError) {
    throw betaError;
  }
  if (!betaRow) {
    return { userId: null, status: 403, error: `Concierge beta is currently limited to invited ${city} testers.` };
  }

  return { userId, status: 200, error: null };
}

async function persistChatBetaLog(
  supabase: ReturnType<typeof createClient>,
  log: ChatBetaLogInsert,
) {
  const { error } = await supabase
    .from("chat_beta_logs")
    .insert({
      user_id: log.user_id,
      city: log.city,
      latest_user_text: log.latest_user_text,
      request_messages: log.request_messages,
      intent_plan: log.intent_plan,
      planner_model: log.planner_model,
      reply_model: log.reply_model,
      planner_raw: log.planner_raw ?? null,
      planner_error: log.planner_error ?? null,
      executed_sql: log.executed_sql,
      query_error: log.query_error ?? null,
      used_fallback: log.used_fallback,
      planner_fallback_used: log.planner_fallback_used,
      query_fallback_used: log.query_fallback_used,
      candidate_ids: log.candidate_ids,
      recommended_ids: log.recommended_ids,
      reply_text: log.reply_text,
      reply_raw: log.reply_raw ?? null,
      reply_error: log.reply_error ?? null,
    });

  if (error) {
    console.error("chat beta log insert failed:", error);
  }
}

async function buildRetrievalPlan(messages: ChatMessage[], now: Date, cutoff: Date) {
  const system = `You rewrite event-search conversations into a standalone retrieval query.

Return JSON only:
{"search_query":"standalone retrieval query","start_time":"ISO timestamp or empty","end_time":"ISO timestamp or empty","notes":"optional short note"}

Rules:
- Preserve the user's actual topic
- Use recent conversation context for short follow-ups like "what about classical guitar"
- Prefer a concise standalone retrieval query, not SQL
- If no explicit time is given, leave start_time and end_time empty
- If time is explicit, keep it inside this range:
  start >= ${now.toISOString()}
  end <= ${cutoff.toISOString()}`;

  const raw = await callAnthropic(system, messages, RETRIEVAL_MODEL, 400);
  const parsed = parseJsonObject(raw) as RetrievalPlan;
  return {
    raw,
    plan: {
      search_query: typeof parsed.search_query === "string" && parsed.search_query.trim()
        ? parsed.search_query.trim()
        : getLatestUserText(messages),
      start_time: typeof parsed.start_time === "string" && parsed.start_time.trim()
        ? new Date(parsed.start_time).toISOString()
        : now.toISOString(),
      end_time: typeof parsed.end_time === "string" && parsed.end_time.trim()
        ? new Date(parsed.end_time).toISOString()
        : cutoff.toISOString(),
      notes: typeof parsed.notes === "string" ? parsed.notes.trim() : "",
    },
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const rawMessages = Array.isArray(body.messages) ? body.messages : [];
    const messages = sanitizeConversationMessages(rawMessages);
    const city = typeof body.city === "string" ? body.city.trim() : "";
    if (!city) {
      return jsonResponse({ error: "city is required" }, 400);
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error("Supabase service credentials are not configured");
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey);
    const betaAccess = await getAuthorizedBetaUserId(req, supabase, city);
    if (!betaAccess.userId) {
      return jsonResponse({ error: betaAccess.error }, betaAccess.status);
    }

    const now = new Date();
    const cutoff = new Date(now);
    cutoff.setUTCDate(cutoff.getUTCDate() + 30);

    let plannerRaw: string | null = null;
    let plannerError: string | null = null;
    let retrievalPlan: RetrievalPlan | null = null;
    let queryErrorMessage: string | null = null;
    let replyRaw: string | null = null;
    let replyError: string | null = null;

    try {
      const built = await buildRetrievalPlan(messages, now, cutoff);
      plannerRaw = built.raw;
      retrievalPlan = built.plan;
    } catch (error) {
      plannerError = errorMessage(error);
      retrievalPlan = {
        search_query: getLatestUserText(messages),
        start_time: now.toISOString(),
        end_time: cutoff.toISOString(),
        notes: "fallback retrieval query",
      };
    }

    const queryEmbedding = await generateQueryEmbedding(retrievalPlan.search_query);
    const { data: rows, error: rpcError } = await supabase.rpc("hybrid_search_events", {
      query_text: retrievalPlan.search_query,
      query_embedding: queryEmbedding,
      filter_city: city,
      window_start: retrievalPlan.start_time,
      window_end: retrievalPlan.end_time,
      match_count: 40,
      full_text_weight: 1,
      semantic_weight: queryEmbedding ? 1 : 0,
      rrf_k: 50,
    });

    if (rpcError) {
      queryErrorMessage = errorMessage(rpcError);
      throw rpcError;
    }

    const candidateEvents = (rows || []) as EventRow[];
    if (!candidateEvents.length) {
      const reply = "I’m not seeing a strong match for that right now.";
      await persistChatBetaLog(supabase, {
        user_id: betaAccess.userId,
        city,
        latest_user_text: getLatestUserText(messages),
        request_messages: messages,
        intent_plan: retrievalPlan,
        planner_model: RETRIEVAL_MODEL,
        reply_model: REPLY_MODEL,
        planner_raw: plannerRaw,
        planner_error: plannerError,
        executed_sql: `rpc hybrid_search_events(query_text=${JSON.stringify(retrievalPlan.search_query)}, city=${JSON.stringify(city)})`,
        query_error: queryErrorMessage,
        used_fallback: plannerError !== null,
        planner_fallback_used: plannerError !== null,
        query_fallback_used: false,
        candidate_ids: [],
        recommended_ids: [],
        reply_text: reply,
        reply_raw: null,
        reply_error: null,
      });
      return jsonResponse({ reply, events: [] });
    }

    const replyPrompt = `You are a calm events concierge for ${city}.

The retrieval query was:
${retrievalPlan.search_query}

Candidate events:
${JSON.stringify(summarizeEvents(candidateEvents.slice(0, 20)))}

Return JSON only:
{"reply":"one short sentence","recommended_ids":[123,456]}

Rules:
- Keep reply to one short sentence
- Recommend at most 4 event ids from the candidate list
- Prefer the strongest direct matches first`;

    let reply = "Here are a few matches.";
    let recommendedIds = candidateEvents.slice(0, 4).map((event) => event.id);

    try {
      const raw = await callAnthropic(replyPrompt, messages, REPLY_MODEL, 400);
      replyRaw = raw;
      const parsed = parseJsonObject(raw) as { reply?: string; recommended_ids?: unknown[] };
      if (typeof parsed.reply === "string" && parsed.reply.trim()) {
        reply = parsed.reply.trim();
      }
      if (Array.isArray(parsed.recommended_ids)) {
        recommendedIds = parsed.recommended_ids
          .map((value) => Number(value))
          .filter((value) => Number.isFinite(value));
      }
    } catch (error) {
      replyError = errorMessage(error);
    }

    const recommendedSet = new Set(recommendedIds);
    const matchedEvents = candidateEvents
      .filter((event) => recommendedSet.has(event.id))
      .slice(0, 4);

    await persistChatBetaLog(supabase, {
      user_id: betaAccess.userId,
      city,
      latest_user_text: getLatestUserText(messages),
      request_messages: messages,
      intent_plan: retrievalPlan,
      planner_model: RETRIEVAL_MODEL,
      reply_model: REPLY_MODEL,
      planner_raw: plannerRaw,
      planner_error: plannerError,
      executed_sql: `rpc hybrid_search_events(query_text=${JSON.stringify(retrievalPlan.search_query)}, city=${JSON.stringify(city)})`,
      query_error: queryErrorMessage,
      used_fallback: plannerError !== null,
      planner_fallback_used: plannerError !== null,
      query_fallback_used: false,
      candidate_ids: candidateEvents.map((event) => event.id),
      recommended_ids: matchedEvents.map((event) => event.id),
      reply_text: reply,
      reply_raw: replyRaw,
      reply_error: replyError,
    });

    return jsonResponse({
      reply,
      events: matchedEvents.length ? matchedEvents : candidateEvents.slice(0, 4),
    });
  } catch (error) {
    console.error("chat-events-rag error:", error);
    return jsonResponse({ error: errorMessage(error) || "Internal server error" }, 500);
  }
});
