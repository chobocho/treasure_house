// #region memory-attach
export function attachPositions(api) {
  if (api.dm_abi_version() !== 1 || api.dm_stride() !== 16) {
    throw new Error('지원하지 않는 위치 ABI');
  }
  const capacity = api.dm_capacity();
  const pointer = api.dm_positions() >>> 0;
  const buffer = api.memory.buffer;
  if (!Number.isInteger(capacity) || capacity < 1 || pointer % 8 !== 0 ||
      pointer + capacity * 16 > buffer.byteLength) {
    throw new Error('위치 배열 범위 오류');
  }
  const values = new DataView(buffer, pointer, capacity * 16);
  // 뷰는 wasm 메모리를 공유한다. JS에서는 읽기만 한다.
  return function snapshot() {
    if (api.memory.buffer !== buffer) throw new Error('메모리 뷰를 다시 연결해야 합니다');
    const count = api.dm_count();
    if (!Number.isInteger(count) || count < 0 || count > capacity) {
      throw new Error('활성 개수 오류');
    }
    const result = [];
    for (let i = 0; i < count; ++i) {
      result.push([values.getFloat64(i * 16, true), values.getFloat64(i * 16 + 8, true)]);
    }
    return result;
  };
}
// #endregion
