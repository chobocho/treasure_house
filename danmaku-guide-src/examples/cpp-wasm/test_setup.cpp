extern "C" unsigned int dm_abi_version();
extern "C" double dm_advance(double position, double speed);

int main() {
  if (dm_abi_version() != 1) return 1;
  if (dm_advance(240.0, 0.0) != 240.0) return 2;
  if (dm_advance(240.0, 4.0) != 244.0) return 3;
  if (dm_advance(0.0, -4.0) != -4.0) return 4;
  if (dm_advance(-10.0, 2.5) != -7.5) return 5;
  if (dm_advance(0.25, 0.5) != 0.75) return 6;
  return 0;
}
