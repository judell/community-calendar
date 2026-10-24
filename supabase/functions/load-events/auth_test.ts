// Tests for the load-events shared-secret gate. Run with:
//   deno test supabase/functions/load-events/auth_test.ts
//
// WHY: the gate is the only thing standing between a public endpoint and
// service-role writes. A missing secret must fail closed, and an unset server
// secret must not be treated as "no secret required".
import { authorize, SECRET_HEADER } from "./auth.ts";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

Deno.test("the header name is the one CI sends", () => {
  assert(SECRET_HEADER === "x-load-events-secret", `got ${SECRET_HEADER}`);
});

Deno.test("accepts the configured secret", () => {
  assert(authorize("s3cret", "s3cret") === "ok", "expected ok");
});

Deno.test("rejects a wrong secret", () => {
  assert(authorize("guess", "s3cret") === "unauthorized", "expected unauthorized");
});

Deno.test("rejects an absent header", () => {
  assert(authorize(null, "s3cret") === "unauthorized", "expected unauthorized");
});

Deno.test("an unset server secret fails closed", () => {
  assert(authorize("s3cret", undefined) === "unconfigured", "expected unconfigured");
  assert(authorize("", undefined) === "unconfigured", "expected unconfigured");
});

Deno.test("an empty configured secret is not a wildcard", () => {
  assert(authorize("", "") === "unconfigured", "expected unconfigured");
});
