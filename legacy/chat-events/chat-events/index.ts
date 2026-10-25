import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-ue-client-tx-id",
};

const SQL_MODEL = "claude-haiku-4-5-20251001";
const REPLY_MODEL = "claude-haiku-4-5-20251001";
const SQL_SOURCE = "public.deduplicated_chat_events";
const CATEGORY_SOURCE = "deduplicated_chat_events";
const CHAT_BETA_CITY = "bloomington";
const SQL_COLUMNS =
  "id, title, start_time, end_time, url, location, description, source, source_urls, category, image_url, all_day, city, merged_ids";
const SQL_TEMPLATE = `SELECT ${SQL_COLUMNS} FROM ${SQL_SOURCE} WHERE city = __CITY__ AND start_time >= __NOW__ AND start_time < __CUTOFF__ ORDER BY start_time ASC LIMIT 12`;
const PARTICIPATION_MODES = ["attend", "participate", "learn", "volunteer", "socialize", "compete"];
const FORMAT_TAGS = [
  "class", "concert", "competition", "ensemble", "event", "exhibition", "festival",
  "hike", "jam", "lecture", "market", "meetup", "open_mic", "reading", "rehearsal",
  "screening", "session", "social", "talk", "tour", "volunteer_shift", "workshop",
];
const AUDIENCE_TAGS = ["adults", "all_ages", "beginners", "families", "kids", "parents", "seniors", "students", "teens"];
const COST_TAGS = ["free", "paid", "donation", "unknown"];
const AUDIENCE_LEAK_TOKENS = new Set([
  ...AUDIENCE_TAGS,
  "adult", "all_age", "allages", "child", "children", "family", "kid", "kid_friendly",
  "kidfriendly", "parent", "senior", "student", "teen", "tween", "tweens", "youth",
]);
const GENERIC_FORMAT_TAGS = new Set(["event"]);
const COMPETITIVE_ACTIVITY_TAGS = new Set([
  "bicycle",
  "bicycling",
  "cycling",
  "fitness",
  "games",
  "running",
  "sports",
]);
const TERM_STOP_WORDS = new Set([
  "a", "an", "the", "and", "or", "but", "for", "with", "near", "around",
  "show", "find", "events", "event", "something", "things", "want", "looking",
  "please", "this", "that", "these", "those", "week", "weekend", "today",
  "tomorrow", "next", "night", "later", "soon", "downtown", "bloomington",
  "what", "about", "any", "activity", "activities",
]);
const FALLBACK_QUERY_ALIASES = [
  { pattern: /\bclassical guitar\b/i, terms: ["classical guitar", "guitar recital", "guitar", "recital"] },
  { pattern: /\bacoustic guitar\b/i, terms: ["acoustic guitar", "acoustic", "guitar", "pickin"] },
];

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
};

type EventFacetContext = {
  id: number;
  title: string;
  location: string | null;
  audience_tags: string[] | null;
};

type IntentPlan = {
  start_time?: string;
  end_time?: string;
  activity_tags?: string[];
  participation_modes?: string[];
  format_tags?: string[];
  audience_tags?: string[];
  cost_tags?: string[];
  text_terms?: string[];
  limit?: number;
  notes?: string;
};

const TOPIC_PIVOT_MAP: Record<string, string[]> = {
  bicycle: ["cycling", "outdoor activities", "recreation"],
  cycling: ["bike-related events", "outdoor activities", "recreation"],
  hiking: ["outdoor activities", "nature activities", "family recreation"],
  nature: ["outdoor activities", "family recreation"],
  outdoors: ["outdoor activities", "family recreation"],
  music: ["live music", "community music"],
  jazz: ["live music", "music events"],
  books: ["library activities", "reading events"],
  talks: ["talks and workshops", "learning events"],
  lecture: ["talks and workshops", "learning events"],
  sports: ["recreation", "outdoor activities"],
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

function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function dayName(d: Date) {
  return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][d.getUTCDay()];
}

function escapeSqlLiteral(value: string) {
  return `'${value.replace(/'/g, "''")}'`;
}

function normalizeToken(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
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

function buildDateGuidance(now: Date) {
  const next = Array.from({ length: 10 }, (_, i) => {
    const d = new Date(now);
    d.setUTCDate(d.getUTCDate() + i);
    return `${dayName(d)} = ${isoDate(d)}`;
  }).join(", ");

  return `Today is ${dayName(now)}, ${isoDate(now)}.
Upcoming dates: ${next}.
"This week" means today through Sunday of the current week.
"This weekend" means Saturday and Sunday of the current week.
"Next week" means Monday through Sunday of the following week.
Use literal ISO dates and timestamps when returning time ranges.`;
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

function normalizeSql(sql: string, city: string, nowIso: string, cutoffIso: string) {
  return sql
    .replace(/__CITY__/g, escapeSqlLiteral(city))
    .replace(/__NOW__/g, `${escapeSqlLiteral(nowIso)}::timestamptz`)
    .replace(/__CUTOFF__/g, `${escapeSqlLiteral(cutoffIso)}::timestamptz`)
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeStringList(values: unknown, allowed?: string[]) {
  if (!Array.isArray(values)) {
    return [];
  }
  const allowedSet = allowed ? new Set(allowed) : null;
  const normalized: string[] = [];
  for (const value of values) {
    if (typeof value !== "string") {
      continue;
    }
    const token = normalizeToken(value);
    if (!token) {
      continue;
    }
    if (allowedSet && !allowedSet.has(token)) {
      continue;
    }
    if (!normalized.includes(token)) {
      normalized.push(token);
    }
  }
  return normalized;
}

function normalizeIsoTimestamp(value: unknown, fallback: string) {
  if (typeof value !== "string" || !value.trim()) {
    return fallback;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? fallback : parsed.toISOString();
}

function buildArrayOverlapClause(column: string, values: string[]) {
  if (!values.length) {
    return "";
  }
  const literals = values.map((value) => escapeSqlLiteral(value)).join(", ");
  return `${column} && ARRAY[${literals}]::text[]`;
}

function buildTextSearchClause(terms: string[]) {
  if (!terms.length) {
    return "";
  }
  const perTerm = terms.map((term) => {
    const like = escapeSqlLiteral(`%${term.replace(/_/g, " ")}%`);
    return `(title ILIKE ${like} OR description ILIKE ${like} OR location ILIKE ${like} OR category ILIKE ${like} OR source ILIKE ${like})`;
  });
  return perTerm.length === 1 ? perTerm[0] : `(${perTerm.join(" OR ")})`;
}

function sanitizeActivityTags(activityTags: string[], audienceTags: string[]) {
  const audienceTokens = new Set([...AUDIENCE_LEAK_TOKENS, ...audienceTags]);
  return activityTags.filter((tag) => !audienceTokens.has(tag));
}

function sanitizeTextTerms(textTerms: string[], audienceTags: string[]) {
  const audienceTokens = new Set([...AUDIENCE_LEAK_TOKENS, ...audienceTags]);
  return textTerms.filter((term) => !audienceTokens.has(term));
}

function normalizeFormatTags(values: unknown) {
  return normalizeStringList(values, FORMAT_TAGS).filter((tag) => !GENERIC_FORMAT_TAGS.has(tag));
}

function shouldExpandParticipateToCompete(plan: Required<IntentPlan>) {
  if (
    !plan.participation_modes.includes("participate") ||
    plan.participation_modes.includes("compete")
  ) {
    return false;
  }
  if (plan.format_tags.includes("competition")) {
    return true;
  }
  if (plan.audience_tags.some((tag) => tag === "kids" || tag === "teens" || tag === "students")) {
    return plan.activity_tags.some((tag) => COMPETITIVE_ACTIVITY_TAGS.has(tag));
  }
  return false;
}

function uniqueStrings(values: string[]) {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized.toLowerCase())) {
      continue;
    }
    seen.add(normalized.toLowerCase());
    result.push(normalized);
  }
  return result;
}

function audiencePhrase(tags: string[]) {
  const set = new Set(tags);
  if (set.has("kids") && set.has("teens")) {
    return "kids and teens";
  }
  if (set.has("kids") && set.has("families")) {
    return "kids and families";
  }
  if (set.has("teens")) {
    return "teens";
  }
  if (set.has("kids")) {
    return "kids";
  }
  if (set.has("families")) {
    return "families";
  }
  if (set.has("students")) {
    return "students";
  }
  return "";
}

function topicSeed(plan: Required<IntentPlan> | null) {
  if (!plan) {
    return "";
  }
  return plan.activity_tags[0] || plan.text_terms[0] || "";
}

function topicLabel(topic: string) {
  switch (topic) {
    case "bicycle":
    case "cycling":
      return "bike-related events";
    case "hiking":
      return "hiking activities";
    case "nature":
    case "outdoors":
      return "outdoor activities";
    case "music":
      return "music events";
    case "jazz":
      return "jazz and live music";
    case "books":
      return "library and reading events";
    case "talks":
    case "lecture":
      return "talks and workshops";
    default:
      return topic ? topic.replace(/_/g, " ") + " events" : "";
  }
}

function buildPivotSuggestions(plan: Required<IntentPlan> | null) {
  if (!plan) {
    return [];
  }
  const topic = topicSeed(plan);
  const audience = audiencePhrase(plan.audience_tags);
  const expansions = topic ? (TOPIC_PIVOT_MAP[topic] || []) : [];
  const suggestions: string[] = [];

  if (topic && audience) {
    suggestions.push(`${topicLabel(topic)} for all ages`);
  }
  if (expansions[0] && audience) {
    suggestions.push(`${expansions[0]} for ${audience}`);
  }
  if (expansions[1] && audience) {
    suggestions.push(`${audience} ${expansions[1]}`);
  }
  if (expansions[2]) {
    suggestions.push(`family-friendly ${expansions[2]}`);
  }
  if (!suggestions.length && topic) {
    suggestions.push(topicLabel(topic));
  }

  return uniqueStrings(suggestions).slice(0, 3);
}

function eventSeriesKey(event: { title: string; location: string | null }) {
  return `${event.title.trim().toLowerCase()}|${(event.location || "").trim().toLowerCase()}`;
}

function audienceMatchLevel(requestedAudiences: string[], eventAudiences: string[] | null | undefined) {
  if (!requestedAudiences.length) {
    return "exact";
  }
  const eventSet = new Set(eventAudiences || []);
  if (requestedAudiences.some((tag) => eventSet.has(tag))) {
    return "exact";
  }
  if (eventSet.has("all_ages")) {
    return "broad";
  }
  if (requestedAudiences.some((tag) => tag === "kids" || tag === "teens")) {
    if (eventSet.has("students") || eventSet.has("families")) {
      return "broad";
    }
  }
  return "none";
}

async function fetchEventFacetContext(
  supabase: ReturnType<typeof createClient>,
  ids: number[],
) {
  if (!ids.length) {
    return new Map<number, EventFacetContext>();
  }
  const { data, error } = await supabase
    .from("deduplicated_chat_events")
    .select("id, title, location, audience_tags")
    .in("id", ids);
  if (error) {
    console.error("event facet context query failed:", error);
    return new Map<number, EventFacetContext>();
  }
  const context = new Map<number, EventFacetContext>();
  for (const row of (data || []) as EventFacetContext[]) {
    context.set(row.id, row);
  }
  return context;
}

function selectRecommendedEvents(
  candidateEvents: EventRow[],
  requestedIds: number[],
  intentPlan: Required<IntentPlan> | null,
  eventContext: Map<number, EventFacetContext>,
) {
  const candidateById = new Map(candidateEvents.map((event) => [event.id, event]));
  const requestedAudiences = intentPlan?.audience_tags || [];
  const selected: EventRow[] = [];
  const seenSeries = new Set<string>();

  const tryAdd = (event: EventRow | undefined) => {
    if (!event) {
      return;
    }
    const key = eventSeriesKey(event);
    if (seenSeries.has(key)) {
      return;
    }
    seenSeries.add(key);
    selected.push(event);
  };

  for (const id of requestedIds) {
    tryAdd(candidateById.get(id));
    if (selected.length >= 4) {
      break;
    }
  }

  if (selected.length < 4) {
    const remaining = candidateEvents
      .filter((event) => !selected.some((selectedEvent) => selectedEvent.id === event.id))
      .sort((a, b) => {
        const aMatch = audienceMatchLevel(requestedAudiences, eventContext.get(a.id)?.audience_tags);
        const bMatch = audienceMatchLevel(requestedAudiences, eventContext.get(b.id)?.audience_tags);
        const score = { exact: 3, broad: 2, none: 1 };
        return score[bMatch] - score[aMatch];
      });

    for (const event of remaining) {
      tryAdd(event);
      if (selected.length >= 4) {
        break;
      }
    }
  }

  return selected.slice(0, 4);
}

function normalizeIntentPlan(rawPlan: unknown, nowIso: string, cutoffIso: string): Required<IntentPlan> {
  const plan = (rawPlan && typeof rawPlan === "object") ? rawPlan as IntentPlan : {};
  const start_time = normalizeIsoTimestamp(plan.start_time, nowIso);
  let end_time = normalizeIsoTimestamp(plan.end_time, cutoffIso);
  if (new Date(end_time).getTime() <= new Date(start_time).getTime()) {
    end_time = cutoffIso;
  }
  const limit = typeof plan.limit === "number" && Number.isFinite(plan.limit)
    ? Math.max(1, Math.min(50, Math.trunc(plan.limit)))
    : 50;
  const audience_tags = normalizeStringList(plan.audience_tags, AUDIENCE_TAGS);
  const activity_tags = sanitizeActivityTags(normalizeStringList(plan.activity_tags), audience_tags);
  const text_terms = sanitizeTextTerms(normalizeStringList(plan.text_terms), audience_tags);
  return {
    start_time,
    end_time,
    activity_tags,
    participation_modes: normalizeStringList(plan.participation_modes, PARTICIPATION_MODES),
    format_tags: normalizeFormatTags(plan.format_tags),
    audience_tags,
    cost_tags: normalizeStringList(plan.cost_tags, COST_TAGS),
    text_terms,
    limit,
    notes: typeof plan.notes === "string" ? plan.notes.trim() : "",
  };
}

type TopicStrategy = "strict" | "fallback";

function buildIntentSql(city: string, plan: Required<IntentPlan>, topicStrategy: TopicStrategy = "strict") {
  const conditions = [
    `city = ${escapeSqlLiteral(city)}`,
    `start_time >= ${escapeSqlLiteral(plan.start_time)}::timestamptz`,
    `start_time < ${escapeSqlLiteral(plan.end_time)}::timestamptz`,
  ];

  const activityClause = buildArrayOverlapClause("activity_tags", plan.activity_tags);
  const textTerms = plan.text_terms.length ? plan.text_terms : plan.activity_tags;
  const textClause = buildTextSearchClause(textTerms);
  if (activityClause) {
    if (topicStrategy === "fallback" && textClause) {
      conditions.push(`(${activityClause} OR ${textClause})`);
    } else {
      conditions.push(activityClause);
    }
  } else if (textClause) {
    conditions.push(textClause);
  }

  const participationClause = buildArrayOverlapClause("participation_modes", plan.participation_modes);
  if (participationClause) {
    conditions.push(participationClause);
  }
  const formatClause = buildArrayOverlapClause("format_tags", plan.format_tags);
  if (formatClause) {
    conditions.push(formatClause);
  }
  const audienceClause = buildArrayOverlapClause("audience_tags", plan.audience_tags);
  if (audienceClause) {
    conditions.push(audienceClause);
  }
  const costClause = buildArrayOverlapClause("cost_tags", plan.cost_tags);
  if (costClause) {
    conditions.push(costClause);
  }

  return `SELECT ${SQL_COLUMNS} FROM ${SQL_SOURCE} WHERE ${conditions.join(" AND ")} ORDER BY start_time ASC LIMIT ${plan.limit}`;
}

function buildRelaxedIntentPlans(plan: Required<IntentPlan>) {
  const variants: Required<IntentPlan>[] = [];
  let current = plan;
  if (current.cost_tags.length) {
    current = {
      ...current,
      cost_tags: [],
    };
    variants.push(current);
  }
  if (current.audience_tags.length) {
    current = {
      ...current,
      audience_tags: [],
    };
    variants.push(current);
  }
  if (current.participation_modes.length) {
    current = {
      ...current,
      participation_modes: [],
    };
    variants.push(current);
  }
  if (current.format_tags.length) {
    current = {
      ...current,
      format_tags: [],
    };
    variants.push(current);
  }
  return variants;
}

function buildQueryVariants(plan: Required<IntentPlan>) {
  const expandedPlan = shouldExpandParticipateToCompete(plan)
    ? { ...plan, participation_modes: uniqueStrings([...plan.participation_modes, "compete"]) }
    : null;
  const relaxedPlans = buildRelaxedIntentPlans(plan);
  const expandedRelaxedPlans = expandedPlan ? buildRelaxedIntentPlans(expandedPlan) : [];
  const variants: Array<{ plan: Required<IntentPlan>; topicStrategy: TopicStrategy }> = [
    { plan, topicStrategy: "strict" },
    ...(expandedPlan ? [{ plan: expandedPlan, topicStrategy: "strict" as const }] : []),
    ...relaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "strict" as const })),
    ...expandedRelaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "strict" as const })),
  ];

  if (plan.activity_tags.length && plan.text_terms.length) {
    variants.push({ plan, topicStrategy: "fallback" });
    if (expandedPlan) {
      variants.push({ plan: expandedPlan, topicStrategy: "fallback" });
    }
    variants.push(...relaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "fallback" as const })));
    variants.push(...expandedRelaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "fallback" as const })));
  }

  return variants.filter((variant, index, all) =>
    all.findIndex((candidate) =>
      candidate.topicStrategy === variant.topicStrategy &&
      JSON.stringify(candidate.plan) === JSON.stringify(variant.plan)
    ) === index
  );
}

function validateSql(sql: string) {
  const normalized = sql.replace(/\s+/g, " ").trim();
  const basePattern = new RegExp(
    `^SELECT ${SQL_COLUMNS.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} FROM ${SQL_SOURCE.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} WHERE .+ ORDER BY start_time ASC LIMIT ([0-9]+)$`,
    "i",
  );
  const match = normalized.match(basePattern);
  if (!match) {
    throw new Error("Generated SQL does not match the allowed shape");
  }
  if (/;|--|\/\*|\*\//.test(normalized)) {
    throw new Error("Generated SQL contains forbidden separators");
  }
  if (/\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|refresh|execute|perform|do|join|union|intersect|except|with)\b/i.test(normalized)) {
    throw new Error("Generated SQL contains forbidden keywords");
  }
  if (!/\bcity\s*=\s*'/.test(normalized) || !/\bstart_time\s*>=\s*'/.test(normalized) || !/\bstart_time\s*<\s*'/.test(normalized)) {
    throw new Error("Generated SQL is missing required filters");
  }
  const limitValue = Number(match[1]);
  if (!Number.isFinite(limitValue) || limitValue < 1 || limitValue > 50) {
    throw new Error("Generated SQL limit is out of range");
  }
  return normalized;
}

function fallbackSql(city: string, nowIso: string, cutoffIso: string) {
  return normalizeSql(SQL_TEMPLATE, city, nowIso, cutoffIso);
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
    all_day: event.all_day,
  }));
}

type DebugInfo = {
  planner_model: string;
  reply_model: string;
  planner_raw?: string | null;
  planner_error?: string | null;
  executed_sql: string;
  query_error?: string | null;
  used_fallback: boolean;
  planner_fallback_used: boolean;
  query_fallback_used: boolean;
  candidate_count: number;
  candidate_titles: string[];
  reply_raw?: string | null;
  reply_error?: string | null;
  recommended_ids?: number[];
};

type ChatBetaLogInsert = {
  user_id: string;
  city: string;
  latest_user_text: string;
  request_messages: ChatMessage[];
  intent_plan: Required<IntentPlan> | null;
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

function getLatestUserText(messages: ChatMessage[]) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === "user" && typeof messages[i].content === "string") {
      return messages[i].content;
    }
  }
  return "";
}

function getSearchTerms(text: string) {
  const aliasTerms = FALLBACK_QUERY_ALIASES
    .filter((alias) => alias.pattern.test(text))
    .flatMap((alias) => alias.terms);
  const words = text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .map((word) => word.trim())
    .filter((word) => word.length >= 3 && !TERM_STOP_WORDS.has(word));
  return uniqueStrings([...aliasTerms, ...words]).slice(0, 6);
}

function buildKeywordFallbackSql(city: string, nowIso: string, cutoffIso: string, text: string) {
  const terms = getSearchTerms(text);
  if (!terms.length) {
    return fallbackSql(city, nowIso, cutoffIso);
  }
  const clauses = terms.map((term) => {
    const like = escapeSqlLiteral(`%${term}%`);
    return `(title ILIKE ${like} OR description ILIKE ${like} OR location ILIKE ${like} OR category ILIKE ${like} OR source ILIKE ${like})`;
  });
  return `SELECT ${SQL_COLUMNS} FROM ${SQL_SOURCE} WHERE city = ${escapeSqlLiteral(city)} AND start_time >= ${escapeSqlLiteral(nowIso)}::timestamptz AND start_time < ${escapeSqlLiteral(cutoffIso)}::timestamptz AND (${clauses.join(" OR ")}) ORDER BY start_time ASC LIMIT 50`;
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
    const nowIso = now.toISOString();
    const cutoffIso = cutoff.toISOString();

    const { data: categoryRows, error: categoryError } = await supabase
      .from(CATEGORY_SOURCE)
      .select("category")
      .eq("city", city)
      .gte("start_time", nowIso)
      .lt("start_time", cutoffIso)
      .limit(5000);

    if (categoryError) {
      throw categoryError;
    }

    const categories = [...new Set((categoryRows || []).map((row: any) => row.category).filter(Boolean))];

    const intentPrompt = `You map a user's request into structured retrieval intent for a community events assistant.

${buildDateGuidance(now)}

Use this table only:
${SQL_SOURCE}(
  id bigint,
  title text,
  start_time timestamptz,
  end_time timestamptz,
  url text,
  location text,
  description text,
  source text,
  source_urls jsonb,
  category text,
  image_url text,
  all_day boolean,
  city text,
  merged_ids bigint[],
  activity_tags text[],
  participation_modes text[],
  format_tags text[],
  audience_tags text[],
  cost_tags text[]
)

Available categories for ${city}: ${categories.join(", ") || "none listed"}.

Return JSON only:
{"start_time":"ISO timestamp","end_time":"ISO timestamp","activity_tags":["music"],"participation_modes":["participate"],"format_tags":["jam"],"audience_tags":["students"],"cost_tags":["free"],"text_terms":["music"],"limit":20,"notes":"optional short note"}

Rules:
- The city is already fixed to ${city}; never ask the user what city.
- start_time and end_time must be literal ISO timestamps inside the upcoming 30-day window when possible
- use participation_modes only from: ${PARTICIPATION_MODES.join(", ")}
- use format_tags only from: ${FORMAT_TAGS.join(", ")}
- use audience_tags only from: ${AUDIENCE_TAGS.join(", ")}
- use cost_tags only from: ${COST_TAGS.join(", ")}
- activity_tags should be short topical tags like music, hiking, nature, books, art, volunteering
- keep audience words like kids, teens, students, families, parents, seniors in audience_tags, not activity_tags
- text_terms should be short topical retrieval terms for title/description matching, not audience words
- only use format_tags when they are specific and helpful; do not use generic values like "event"
- if the user says "what about ..." or another short follow-up, treat it as a refinement of the recent conversation topic, not a literal search for filler words
- if the user is vague, return a broad upcoming intent rather than asking for clarification
- Return JSON only, never prose or follow-up questions`;

    let sql = fallbackSql(city, nowIso, cutoffIso);
    let plannerRaw: string | null = null;
    let plannerError: string | null = null;
    let queryErrorMessage: string | null = null;
    let plannerFallbackUsed = false;
    let queryFallbackUsed = false;
    const latestUserText = getLatestUserText(messages);
    let normalizedPlan: Required<IntentPlan> | null = null;

    try {
      const rawIntentPlan = await callAnthropic(intentPrompt, messages, SQL_MODEL, 512);
      plannerRaw = rawIntentPlan;
      const parsedPlan = parseJsonObject(rawIntentPlan);
      normalizedPlan = normalizeIntentPlan(parsedPlan, nowIso, cutoffIso);
      sql = validateSql(buildIntentSql(city, normalizedPlan, "strict"));
    } catch (error) {
      console.error("SQL planning failed, using fallback:", error);
      plannerError = errorMessage(error);
      plannerFallbackUsed = true;
      sql = buildKeywordFallbackSql(city, nowIso, cutoffIso, latestUserText);
    }

    const { data: candidateEvents, error: queryError } = await supabase.rpc("run_chat_events_sql", {
      query: sql,
    });

    if (queryError) {
      console.error("Query execution failed, retrying with fallback:", queryError);
      queryErrorMessage = errorMessage(queryError);
      queryFallbackUsed = true;
      const { data: fallbackEvents, error: fallbackError } = await supabase.rpc("run_chat_events_sql", {
        query: buildKeywordFallbackSql(city, nowIso, cutoffIso, latestUserText),
      });
      if (fallbackError) {
        throw fallbackError;
      }
      const events = (fallbackEvents || []) as EventRow[];
      const executedSql = buildKeywordFallbackSql(city, nowIso, cutoffIso, latestUserText);
      return await finishResponse(supabase, betaAccess.userId, messages, city, categories, events, executedSql, normalizedPlan, {
        planner_model: SQL_MODEL,
        reply_model: REPLY_MODEL,
        planner_raw: plannerRaw,
        planner_error: plannerError,
        executed_sql: executedSql,
        query_error: queryErrorMessage,
        used_fallback: plannerFallbackUsed || queryFallbackUsed,
        planner_fallback_used: plannerFallbackUsed,
        query_fallback_used: queryFallbackUsed,
        candidate_count: events.length,
        candidate_titles: events.map((event) => event.title),
      });
    }

    let events = (candidateEvents || []) as EventRow[];
    if (!events.length && normalizedPlan && !plannerFallbackUsed) {
      for (const variant of buildQueryVariants(normalizedPlan).slice(1)) {
        const variantSql = validateSql(buildIntentSql(city, variant.plan, variant.topicStrategy));
        const { data: relaxedEvents, error: relaxedError } = await supabase.rpc("run_chat_events_sql", {
          query: variantSql,
        });
        if (relaxedError) {
          continue;
        }
        const candidateRelaxed = (relaxedEvents || []) as EventRow[];
        if (candidateRelaxed.length) {
          queryFallbackUsed = true;
          sql = variantSql;
          events = candidateRelaxed;
          break;
        }
      }
    }
    return await finishResponse(supabase, betaAccess.userId, messages, city, categories, events, sql, normalizedPlan, {
      planner_model: SQL_MODEL,
      reply_model: REPLY_MODEL,
      planner_raw: plannerRaw,
      planner_error: plannerError,
      executed_sql: sql,
      query_error: queryErrorMessage,
      used_fallback: plannerFallbackUsed || queryFallbackUsed,
      planner_fallback_used: plannerFallbackUsed,
      query_fallback_used: queryFallbackUsed,
      candidate_count: events.length,
      candidate_titles: events.map((event) => event.title),
    });
  } catch (error) {
    console.error("chat-events error:", error);
    return jsonResponse({ error: errorMessage(error) || "Internal server error" }, 500);
  }
});

async function finishResponse(
  supabase: ReturnType<typeof createClient>,
  userId: string,
  messages: ChatMessage[],
  city: string,
  categories: string[],
  candidateEvents: EventRow[],
  sql: string,
  intentPlan: Required<IntentPlan> | null,
  debug: DebugInfo,
) {
  const pivotSuggestions = candidateEvents.length ? [] : buildPivotSuggestions(intentPlan);
  if (!candidateEvents.length) {
    const reply = pivotSuggestions.length
      ? "I’m not seeing a strong match for that, but I can widen the search in a nearby direction."
      : "I’m not seeing a strong match for that right now.";

    await persistChatBetaLog(supabase, {
      user_id: userId,
      city,
      latest_user_text: getLatestUserText(messages),
      request_messages: messages,
      intent_plan: intentPlan,
      planner_model: debug.planner_model,
      reply_model: debug.reply_model,
      planner_raw: debug.planner_raw ?? null,
      planner_error: debug.planner_error ?? null,
      executed_sql: sql,
      query_error: debug.query_error ?? null,
      used_fallback: debug.used_fallback,
      planner_fallback_used: debug.planner_fallback_used,
      query_fallback_used: debug.query_fallback_used,
      candidate_ids: [],
      recommended_ids: [],
      reply_text: reply,
      reply_raw: null,
      reply_error: null,
    });

    return jsonResponse({
      reply,
      events: [],
      pivot_suggestions: pivotSuggestions,
    });
  }

  const eventContext = await fetchEventFacetContext(
    supabase,
    candidateEvents.map((event) => event.id),
  );
  const requestedAudiences = intentPlan?.audience_tags || [];
  const audienceContext = candidateEvents.map((event) => {
    const meta = eventContext.get(event.id);
    return {
      id: event.id,
      title: event.title,
      audience_tags: meta?.audience_tags || [],
      audience_match: audienceMatchLevel(requestedAudiences, meta?.audience_tags),
    };
  });
  const exactAudienceCount = audienceContext.filter((item) => item.audience_match === "exact").length;
  const broadAudienceCount = audienceContext.filter((item) => item.audience_match === "broad").length;

  const replyPrompt = `You are a calm events concierge for ${city}.

The backend already ran this retrieval query:
${sql}

Candidate events:
${JSON.stringify(summarizeEvents(candidateEvents))}

Audience match context:
${JSON.stringify(audienceContext)}

Available categories in this city: ${categories.join(", ") || "none listed"}.

Return JSON only in this format:
{"reply":"one short sentence","recommended_ids":[123,456]}

Rules:
- Keep reply to one short sentence
- Do not list event details in the reply; event cards render separately
- Recommend at most 4 events by exact numeric id from the candidate list
- If there are few or no good matches, recommended_ids can be []
- Requested audience tags: ${requestedAudiences.join(", ") || "none"}
- Exact audience matches available: ${exactAudienceCount}
- Broader audience matches available: ${broadAudienceCount}
- If you recommend broader all-ages, student, or family options instead of exact audience matches, say that explicitly
- Stay conversational and do not redirect the user to categories
- Prefer recommending over asking follow-up questions`;

  let reply = candidateEvents.length
    ? "Here are a few matches."
    : "I did not find a strong match in the current window.";
  let recommendedIds: number[] = candidateEvents.slice(0, 4).map((event) => event.id);
  let replyRaw: string | null = null;
  let replyError: string | null = null;

  try {
    const rawReply = await callAnthropic(replyPrompt, messages, REPLY_MODEL, 512);
    replyRaw = rawReply;
    const parsedReply = parseJsonObject(rawReply);
    if (typeof parsedReply.reply === "string" && parsedReply.reply.trim()) {
      reply = parsedReply.reply.trim();
    }
    if (Array.isArray(parsedReply.recommended_ids)) {
      recommendedIds = parsedReply.recommended_ids
        .map((value: unknown) => Number(value))
        .filter((value: number) => Number.isFinite(value));
    }
  } catch (error) {
    console.error("Reply generation failed, using fallback:", error);
    replyError = errorMessage(error);
  }

  const matchedEvents = selectRecommendedEvents(candidateEvents, recommendedIds, intentPlan, eventContext);

  await persistChatBetaLog(supabase, {
    user_id: userId,
    city,
    latest_user_text: getLatestUserText(messages),
    request_messages: messages,
    intent_plan: intentPlan,
    planner_model: debug.planner_model,
    reply_model: debug.reply_model,
    planner_raw: debug.planner_raw ?? null,
    planner_error: debug.planner_error ?? null,
    executed_sql: sql,
    query_error: debug.query_error ?? null,
    used_fallback: debug.used_fallback,
    planner_fallback_used: debug.planner_fallback_used,
    query_fallback_used: debug.query_fallback_used,
    candidate_ids: candidateEvents.map((event) => event.id),
    recommended_ids: matchedEvents.map((event) => event.id),
    reply_text: reply,
    reply_raw: replyRaw,
    reply_error: replyError,
  });

  return jsonResponse({
    reply,
    events: matchedEvents,
    pivot_suggestions: [],
  });
}
