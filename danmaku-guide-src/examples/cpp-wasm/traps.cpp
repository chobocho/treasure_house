// #region wasm-traps
// 게임이 아닌 오류 진단 전용 모듈이다. JS에서 예외 종류를 확인한다.
extern "C" __attribute__((export_name("dm_trap"))) void dm_trap() {
  __builtin_trap();
}
extern "C" __attribute__((export_name("dm_read"))) unsigned int dm_read(unsigned int address) {
  return *reinterpret_cast<volatile unsigned int*>(address);
}
// #endregion
