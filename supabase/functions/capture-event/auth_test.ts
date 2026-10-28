// Tests for the capture-event auth gate (GHSA-qq24-wmxg-hrgv). Run with:
//   deno test supabase/functions/capture-event/auth_test.ts
//
// WHY: extract forwards uploads to paid Anthropic/OpenAI APIs. A request with
// no user token must be refused before any outbound call.
import { handler } from "./index.ts";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

Deno.test("extract without a token returns 401 with no outbound fetch", async () => {
  const originalFetch = globalThis.fetch;
  let fetchCalls = 0;
  globalThis.fetch = (() => {
    fetchCalls++;
    throw new Error("unexpected outbound fetch");
  }) as typeof fetch;

  try {
    const form = new FormData();
    form.append("mode", "extract");
    form.append("file", new File(["poster"], "poster.jpg", { type: "image/jpeg" }));

    const req = new Request("http://localhost/functions/v1/capture-event", {
      method: "POST",
      body: form,
    });
    const resp = await handler(req);

    assert(resp.status === 401, `expected 401, got ${resp.status}`);
    assert(fetchCalls === 0, `expected no outbound fetch, got ${fetchCalls}`);
    const body = await resp.json();
    assert(body.error === "Missing authorization", `unexpected error: ${body.error}`);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
