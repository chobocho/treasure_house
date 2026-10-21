// #region input-map
const bindings: Record<string, number> = { ArrowLeft: 1, KeyA: 1, ArrowRight: 2, KeyD: 2,
  ArrowUp: 4, KeyW: 4, ArrowDown: 8, KeyS: 8, KeyZ: 16, Space: 16,
  ShiftLeft: 32, ShiftRight: 32, KeyX: 64, Enter: 128, KeyP: 256 };
// #endregion

// #region input-bind
export function bindInput(canvas: HTMLCanvasElement) {
  const keys = new Set<string>();
  canvas.tabIndex = 0;
  const down = (e: KeyboardEvent) => {
    if (bindings[e.code]) { e.preventDefault(); keys.add(e.code); }
  };
  const up = (e: KeyboardEvent) => { keys.delete(e.code); };
  const blur = () => keys.clear();
  canvas.addEventListener('keydown', down);
  canvas.addEventListener('keyup', up);
  canvas.addEventListener('blur', blur);
  return {
    read(): number {
      let bits = 0;
      for (const code of keys) bits |= bindings[code];
      return bits;
    },
    dispose(): void {
      canvas.removeEventListener('keydown', down);
      canvas.removeEventListener('keyup', up);
      canvas.removeEventListener('blur', blur);
      keys.clear();
    }
  };
}
// #endregion
