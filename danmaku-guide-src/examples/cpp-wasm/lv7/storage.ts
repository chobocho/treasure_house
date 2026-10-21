// #region best-valid
function validBest(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}
export function safeStorage(): Storage | null {
  try { return globalThis.localStorage; } catch { return null; }
}
// #endregion

// #region best-load
export function loadBest(storage: Pick<Storage, 'getItem'> | null): number {
  try {
    const data = JSON.parse(storage?.getItem('danmaku-wasm-best') ?? 'null');
    return validBest(data?.best) ? data.best : 0;
  } catch { return 0; }
}
// #endregion

// #region best-save
export function saveBest(storage: Pick<Storage, 'setItem'> | null, value: unknown): boolean {
  if (!storage || !validBest(value)) return false;
  try {
    storage.setItem('danmaku-wasm-best', JSON.stringify({ best: value }));
    return true;
  } catch { return false; }
}
// #endregion
