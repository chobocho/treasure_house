// 고치기 전의 asInts — agents/common.ts 의 2026-10-18 판을 그대로
// 옮겼다. 16/test_ints_old.ts 가 이것을 시험한다(RED).
export function asInts(d: Record<string, unknown>, ...keys: string[]) {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(d)) {
    out[k] = keys.includes(k) ? Math.trunc(Number(v)) : v;
  }
  return out;
}
//@ norun
