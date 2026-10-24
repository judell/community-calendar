/** Shared-secret gate for load-events (GHSA-qmc5-6cfg-38p7).
 *
 * The gateway's JWT check was never an authorization boundary here: the
 * publishable key ships in xmlui/config.json, so anyone can satisfy it.
 * Only CI holds this secret.
 */
export const SECRET_HEADER = "x-load-events-secret";

export type AuthResult = "ok" | "unauthorized" | "unconfigured";

export function authorize(
  provided: string | null,
  expected: string | undefined,
): AuthResult {
  // Fail closed: a deploy that forgot the secret must not reopen the write path.
  if (!expected) return "unconfigured";
  return provided === expected ? "ok" : "unauthorized";
}
