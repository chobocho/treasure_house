// #region memory-layout
#if defined(__wasm__)
#define DM_API(name) extern "C" __attribute__((export_name(#name), used))
#else
#define DM_API(name) extern "C"
#endif
constexpr unsigned int CAPACITY = 4;
alignas(8) static double positions[CAPACITY * 2];
static unsigned int count;
DM_API(dm_abi_version) unsigned int dm_abi_version() { return 1; }
DM_API(dm_positions) const double* dm_positions() { return positions; }
DM_API(dm_count) unsigned int dm_count() { return count; }
DM_API(dm_capacity) unsigned int dm_capacity() { return CAPACITY; }
DM_API(dm_stride) unsigned int dm_stride() { return 16; }
// #endregion

// #region memory-init
DM_API(dm_init) void dm_init() {
  count = 0;
  for (unsigned int i = 0; i < CAPACITY * 2; ++i) positions[i] = 0;
}
DM_API(dm_push) unsigned int dm_push(double x, double y) {
  if (count == CAPACITY) return 0;
  positions[count * 2] = x;
  positions[count * 2 + 1] = y;
  ++count;
  return 1;
}
// #endregion

// #region memory-step
DM_API(dm_shift) void dm_shift(double dx, double dy) {
  for (unsigned int i = 0; i < count; ++i) {
    positions[i * 2] += dx;
    positions[i * 2 + 1] += dy;
  }
}
// #endregion
