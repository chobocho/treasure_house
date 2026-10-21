// #region lv1-adapter
export function attachGame(api, seed) {
  if (api.dm_abi_version() !== 1) throw new Error('지원하지 않는 게임 ABI');
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) throw new Error('잘못된 시드');
  api.dm_init(seed);
  return {
    step(bits) {
      if (!Number.isInteger(bits) || bits < 0 || bits > 511) throw new Error('잘못된 입력 비트');
      if (api.dm_step(bits) !== 1) throw new Error('wasm 스텝 거부');
    },
    snapshot() {
      return { frame: api.dm_frame(), bullets: api.dm_count(), enemies: 0,
        score: 0, lives: 3, phase: 0, checksum: api.dm_checksum() >>> 0 };
    }
  };
}
// #endregion
