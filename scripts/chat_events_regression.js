const AUDIENCE_TAGS = ["adults", "all_ages", "beginners", "families", "kids", "parents", "seniors", "students", "teens"];
const PARTICIPATION_MODES = ["attend", "participate", "learn", "volunteer", "socialize", "compete"];
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

function uniqueStrings(values) {
  const seen = new Set();
  const result = [];
  for (const value of values) {
    const normalized = String(value || "").trim();
    if (!normalized || seen.has(normalized.toLowerCase())) continue;
    seen.add(normalized.toLowerCase());
    result.push(normalized);
  }
  return result;
}

function sanitizeConversationMessages(rawMessages) {
  return rawMessages.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const { role, content } = item;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string" || !content.trim()) {
      return [];
    }
    return [{ role, content: content.trim() }];
  });
}

function getSearchTerms(text) {
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

function shouldExpandParticipateToCompete(plan) {
  if (!plan.participation_modes.includes("participate") || plan.participation_modes.includes("compete")) {
    return false;
  }
  if ((plan.format_tags || []).includes("competition")) {
    return true;
  }
  if ((plan.audience_tags || []).some((tag) => tag === "kids" || tag === "teens" || tag === "students")) {
    return (plan.activity_tags || []).some((tag) => COMPETITIVE_ACTIVITY_TAGS.has(tag));
  }
  return false;
}

function buildRelaxedIntentPlans(plan) {
  const variants = [];
  let current = { ...plan };
  if (current.cost_tags.length) {
    current = { ...current, cost_tags: [] };
    variants.push(current);
  }
  if (current.audience_tags.length) {
    current = { ...current, audience_tags: [] };
    variants.push(current);
  }
  if (current.participation_modes.length) {
    current = { ...current, participation_modes: [] };
    variants.push(current);
  }
  if (current.format_tags.length) {
    current = { ...current, format_tags: [] };
    variants.push(current);
  }
  return variants;
}

function buildQueryVariants(plan) {
  const expandedPlan = shouldExpandParticipateToCompete(plan)
    ? { ...plan, participation_modes: uniqueStrings([...plan.participation_modes, "compete"]) }
    : null;
  const relaxedPlans = buildRelaxedIntentPlans(plan);
  const expandedRelaxedPlans = expandedPlan ? buildRelaxedIntentPlans(expandedPlan) : [];
  const variants = [
    { plan, topicStrategy: "strict" },
    ...(expandedPlan ? [{ plan: expandedPlan, topicStrategy: "strict" }] : []),
    ...relaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "strict" })),
    ...expandedRelaxedPlans.map((relaxedPlan) => ({ plan: relaxedPlan, topicStrategy: "strict" })),
  ];
  return variants.filter((variant, index, all) =>
    all.findIndex((candidate) =>
      candidate.topicStrategy === variant.topicStrategy &&
      JSON.stringify(candidate.plan) === JSON.stringify(variant.plan)
    ) === index
  );
}

function expect(name, condition, detail) {
  const status = condition ? "PASS" : "FAIL";
  console.log(`${status} ${name}`);
  if (!condition && detail) console.log(`  ${detail}`);
  return condition;
}

let passed = 0;
let total = 0;

const rawMessages = [
  { role: "user", content: "acoustic guitar" },
  {
    role: "assistant",
    content: "Great news—we have several acoustic performances coming up.",
    events: [{ id: 1, title: "Irish Music Session" }],
  },
  { role: "user", content: " what about classical guitar " },
  { role: "assistant", events: [{ id: 2 }] },
];
const sanitized = sanitizeConversationMessages(rawMessages);
total += 1; passed += expect(
  "sanitizeConversationMessages strips extra fields and invalid assistant payloads",
  sanitized.length === 3 &&
    sanitized[1].role === "assistant" &&
    sanitized[1].content === "Great news—we have several acoustic performances coming up." &&
    sanitized[2].content === "what about classical guitar",
  JSON.stringify(sanitized, null, 2),
) ? 1 : 0;

const classicalTerms = getSearchTerms("what about classical guitar");
total += 1; passed += expect(
  "getSearchTerms removes filler and expands classical guitar",
  !classicalTerms.includes("what") &&
    !classicalTerms.includes("about") &&
    classicalTerms.includes("classical guitar") &&
    classicalTerms.includes("guitar recital") &&
    classicalTerms.includes("guitar") &&
    classicalTerms.includes("recital"),
  JSON.stringify(classicalTerms),
) ? 1 : 0;

const bicycleTerms = getSearchTerms("any bicycle activities for kids/teens?");
total += 1; passed += expect(
  "getSearchTerms removes generic filler from bicycle youth query",
  !bicycleTerms.includes("any") &&
    !bicycleTerms.includes("activities") &&
    bicycleTerms.includes("bicycle") &&
    bicycleTerms.includes("kids") &&
    bicycleTerms.includes("teens"),
  JSON.stringify(bicycleTerms),
) ? 1 : 0;

const variants = buildQueryVariants({
  start_time: "2026-04-21T00:00:00.000Z",
  end_time: "2026-05-21T23:59:59.000Z",
  activity_tags: ["cycling"],
  participation_modes: ["participate"],
  format_tags: [],
  audience_tags: ["kids", "teens"],
  cost_tags: [],
  text_terms: ["bike", "cycling"],
  limit: 20,
  notes: "cycling activities for children and teenagers",
});
total += 1; passed += expect(
  "buildQueryVariants inserts participate+compete variant before dropping participation",
  variants.length >= 2 &&
    JSON.stringify(variants[1].plan.participation_modes) === JSON.stringify(["participate", "compete"]) &&
    variants.some((variant) => JSON.stringify(variant.plan.participation_modes) === JSON.stringify([])),
  JSON.stringify(variants.map((variant) => variant.plan.participation_modes)),
) ? 1 : 0;

console.log(`\n${passed}/${total} regression checks passed`);
process.exit(passed === total ? 0 : 1);
