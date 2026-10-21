// #region lv6-adapter
export function attachGame(api, seed, data = []) {
  if (api.dm_abi_version() !== 1) throw new Error('지원하지 않는 게임 ABI');
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) throw new Error('잘못된 시드');
  const stage = validateStage(data);
  api.dm_init(seed);
  for (const [frame, kind, pattern] of stage) {
    if (api.dm_stage_add(frame, kind === 'enemy' ? 0 : 1, pattern) !== 1) throw new Error('wasm 스테이지 거부');
  }
  return {
    stage,
    step(bits) {
      if (!Number.isInteger(bits) || bits < 0 || bits > 511) throw new Error('잘못된 입력 비트');
      if (api.dm_step(bits) !== 1) throw new Error('wasm 스텝 거부');
    },
    snapshot() {
      return { frame: api.dm_frame(), bullets: api.dm_count(), enemies: api.dm_enemies(),
        score: api.dm_score(), lives: api.dm_lives(), phase: api.dm_phase(), checksum: api.dm_checksum() >>> 0 };
    }
  };
}
// #endregion

// #region lv6-stage-validate
export function validateStage(data) {
  if (!Array.isArray(data) || data.length > 4096) throw new Error('잘못된 스테이지 배열');
  const result = [];
  let previous = -1;
  for (const e of data) {
    if (!e || typeof e !== 'object' || Array.isArray(e)) throw new Error('잘못된 이벤트');
    const { frame, kind } = e;
    if (!Number.isInteger(frame) || frame < 0 || frame < previous) throw new Error('잘못된 시간');
    if (kind !== 'enemy' && kind !== 'boss') throw new Error('잘못된 종류');
    const keys = Object.keys(e), expected = kind === 'enemy' ? ['frame', 'kind', 'pattern'] : ['frame', 'kind'];
    if (keys.length !== expected.length || !expected.every((key) => keys.includes(key))) throw new Error('잘못된 필드');
    const pattern = kind === 'enemy' ? e.pattern : 0;
    if (!Number.isInteger(pattern) || pattern < 0 || pattern > 3) throw new Error('잘못된 패턴');
    result.push(Object.freeze([frame, kind, pattern]));
    previous = frame;
  }
  return Object.freeze(result);
}
// #endregion
