#include <cassert>
extern "C" void dm_init();
extern "C" unsigned int dm_push(double, double);
extern "C" unsigned int dm_count();
extern "C" const double* dm_positions();
extern "C" void dm_shift(double, double);
int main() {
  dm_init();
  assert(dm_count() == 0);
  for (unsigned int i = 0; i < 4; ++i) assert(dm_push(i, -2.5) == 1);
  assert(dm_push(99, 99) == 0);
  assert(dm_count() == 4);
  dm_shift(-0.5, 4);
  assert(dm_positions()[0] == -0.5);
  assert(dm_positions()[7] == 1.5);
  dm_init();
  assert(dm_count() == 0 && dm_positions()[0] == 0);
}
