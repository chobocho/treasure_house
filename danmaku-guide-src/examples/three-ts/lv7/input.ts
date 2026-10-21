// #region input-map
const bindings: Record<string, number> = { ArrowLeft: 1, KeyA: 1, ArrowRight: 2, KeyD: 2,
  ArrowUp: 4, KeyW: 4, ArrowDown: 8, KeyS: 8, KeyZ: 16, Space: 16,
  ShiftLeft: 32, ShiftRight: 32, KeyX: 64, Enter: 128, KeyP: 256 };
const controls = 64 | 128 | 256;
// #endregion

// #region input-bind
export function bindInput(canvas: HTMLCanvasElement) {
  const keys = new Set<string>();
  let pending = 0, previousPulse = 0;
  canvas.tabIndex = 0;
  const down = (e: KeyboardEvent) => {
    const bit = bindings[e.code];
    if (!bit) return;
    e.preventDefault(); e.stopPropagation();
    if (!keys.has(e.code)) pending |= bit & controls;
    keys.add(e.code);
  };
  const up = (e: KeyboardEvent) => { keys.delete(e.code); };
  const blur = () => { keys.clear(); pending = 0; previousPulse = 0; };
  canvas.addEventListener('keydown', down);
  canvas.addEventListener('keyup', up);
  canvas.addEventListener('blur', blur);
  // #endregion
  return {
    // #region input-read
    read(): number {
      let bits = 0;
      for (const code of keys) bits |= bindings[code] & ~controls;
      // 짧은 눌림을 논리 스텝까지 보관하고 연속 눌림 사이에는 낮은 비트를 한 번 전달한다.
      const pulse = pending & ~previousPulse;
      pending &= ~pulse; previousPulse = pulse;
      return bits | pulse;
    },
    // #endregion
    // #region input-close
    dispose(): void {
      canvas.removeEventListener('keydown', down);
      canvas.removeEventListener('keyup', up);
      canvas.removeEventListener('blur', blur);
      blur();
    }
    // #endregion
  };
}
