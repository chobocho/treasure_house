// #region setup-exports
// 같은 계산을 검증하도록 네이티브에서는 wasm 전용 속성만 제외한다.
#if defined(__wasm__)
#define DM_EXPORT(name) extern "C" __attribute__((export_name(#name), used))
#else
#define DM_EXPORT(name) extern "C"
#endif

static_assert(sizeof(unsigned int) == 4);
static_assert(sizeof(double) == 8);

DM_EXPORT(dm_abi_version) unsigned int dm_abi_version() {
  return 1;
}
// #endregion

// #region setup-advance
// 속도는 고정 스텝당 변위다. 설치 검사에서는 화면 경계나 게임 규칙을 넣지 않는다.
DM_EXPORT(dm_advance) double dm_advance(double position, double speed) {
  return position + speed;
}
// #endregion
