/** Sources the stale sweep may delete from (issue #233). */
export function resolveSweepScope(
  ranSources: string[] | undefined,
  presentSources: string[],
): string[] {
  // An absent manifest means the caller predates #233, so fall back to the
  // sources visible in the payload. A present-but-empty manifest means
  // nothing ran and must not sweep anything.
  return ranSources ?? presentSources;
}
