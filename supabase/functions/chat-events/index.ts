import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-ue-client-tx-id",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages, city } = await req.json();

    // Fetch next 30 days of events for this city
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const now = new Date();
    const thirtyDaysOut = new Date(now);
    thirtyDaysOut.setDate(thirtyDaysOut.getDate() + 30);

    const { data: events } = await supabase
      .from("events")
      .select("title, start_time, end_time, location, category, source, url")
      .eq("city", city)
      .gte("start_time", now.toISOString())
      .lte("start_time", thirtyDaysOut.toISOString())
      .order("start_time", { ascending: true })
      .limit(1000);

    const eventSummary = (events || [])
      .map(
        (e) =>
          `${e.title} | ${e.start_time} | ${e.location || "TBD"} | ${e.category || ""}`
      )
      .join("\n");

    const categories = [
      ...new Set((events || []).map((e) => e.category).filter(Boolean)),
    ];

    const today = now.toISOString().substring(0, 10);
    const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const todayDay = dayNames[now.getDay()];

    const systemPrompt = `You are a friendly events concierge for ${city}. Today is ${todayDay}, ${today}. You have ${(events || []).length} upcoming events spanning the next 30 days across these categories: ${categories.join(", ")}.

Here are the events:
${eventSummary}

Help the user discover events by asking about:
1. What categories or types of events interest them
2. When they want to attend (today, this weekend, next week, etc.)
3. What area or how far they are willing to travel

Date guidance:
- "This week" means today (${todayDay}) through Sunday of the current week.
- "This weekend" means Saturday and Sunday of the current week.
- "Next week" means Monday through Sunday of the following week.
- Be strict about date boundaries — do not include events outside the requested range.

Be conversational and concise. Recommend events eagerly — don't over-ask. If the user gives you enough to work with (e.g. a category, a timeframe, or a vibe), recommend matching events right away. You can always refine in follow-up turns. When the user says something doesn't work (too far, wrong vibe), pivot immediately with alternatives.

IMPORTANT: Always respond with valid JSON in this exact format:
{"reply": "your conversational response here", "recommended_titles": ["Exact Event Title 1", "Exact Event Title 2"]}

Rules for the reply and recommended_titles:
- Do NOT describe or list event details (title, date, time, location) in the "reply" text. The events will be displayed as cards automatically. Your reply should only contain brief conversational context like "Here are some intimate jazz events this week:" or follow-up questions.
- Put ALL events you want to recommend in the "recommended_titles" array using the EXACT title from the event list above. Every event you mention must be in this array.
- If you are not yet recommending specific events (e.g. still asking questions), use an empty array []. But prefer recommending over asking.`;

    const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
    if (!anthropicKey) throw new Error("ANTHROPIC_API_KEY not configured");

    const cleanMessages = messages.map(({ role, content }: any) => ({ role, content }));

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": anthropicKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 1024,
        system: systemPrompt,
        messages: cleanMessages,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Anthropic API error:", errorText);
      throw new Error(`Anthropic API error: ${response.status}`);
    }

    const result = await response.json();
    const rawText =
      result.content?.find((c: any) => c.type === "text")?.text ||
      "Sorry, I could not generate a response.";

    let reply = rawText;
    let matchedEvents: any[] = [];

    // Try to parse JSON, stripping markdown code fences if present
    let jsonText = rawText.trim();
    if (jsonText.startsWith("```")) {
      jsonText = jsonText.replace(/^```(?:json)?\n?/, "").replace(/\n?```$/, "");
    }

    try {
      const parsed = JSON.parse(jsonText);
      if (parsed.reply) {
        reply = parsed.reply;
        const titles = parsed.recommended_titles || [];
        if (titles.length > 0 && events) {
          const titleSet = new Set(titles.map((t: string) => t.toLowerCase()));
          matchedEvents = events.filter((e) =>
            titleSet.has(e.title.toLowerCase())
          );
        }
      }
    } catch {
      // Try to extract JSON from the response
      const jsonMatch = jsonText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          const parsed = JSON.parse(jsonMatch[0]);
          if (parsed.reply) {
            reply = parsed.reply;
            const titles = parsed.recommended_titles || [];
            if (titles.length > 0 && events) {
              const titleSet = new Set(titles.map((t: string) => t.toLowerCase()));
              matchedEvents = events.filter((e) =>
                titleSet.has(e.title.toLowerCase())
              );
            }
          }
        } catch {
          // Truly unparseable, use raw text
        }
      }
    }

    return new Response(JSON.stringify({ reply, events: matchedEvents }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ error: error.message || "Internal server error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
