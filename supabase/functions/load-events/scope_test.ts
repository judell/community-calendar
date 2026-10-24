// Tests for the stale-sweep scope. Run with:
//   deno test supabase/functions/load-events/scope_test.ts
//
// WHY: an absent manifest must keep the pre-#233 fallback, and a present but
// empty manifest must sweep nothing. Getting either branch wrong either
// deletes a failed source's rows or leaves a quiet source's rows forever.
import { resolveSweepScope } from "./scope.ts";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

Deno.test("falls back to payload sources when the manifest is absent", () => {
  const scope = resolveSweepScope(undefined, ["src-a", "src-b"]);
  assert(scope.join(",") === "src-a,src-b", `got ${scope}`);
});

Deno.test("a present but empty manifest sweeps nothing", () => {
  const scope = resolveSweepScope([], ["src-a"]);
  assert(scope.length === 0, `got ${scope}`);
});

Deno.test("a manifest scopes the sweep to the sources that ran", () => {
  const scope = resolveSweepScope(["src-quiet"], ["src-a"]);
  assert(scope.join(",") === "src-quiet", `got ${scope}`);
});

Deno.test("a manifest is not merged with the payload sources", () => {
  // src-a has events but did not run: the sweep must leave it alone.
  const scope = resolveSweepScope(["src-quiet"], ["src-a"]);
  assert(!scope.includes("src-a"), `got ${scope}`);
});
