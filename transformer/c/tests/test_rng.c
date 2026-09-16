/* test_rng.c — SPEC.md §1 의 고정값.
 * py/transformerlib/tests/test_rng.py
 * 와 **같은 상수**다. 여기가 어긋나면 초기화도 배치도 파이썬과 달라져
 * 9부의 대조가 처음부터 무너진다. */
#include "check.h"
#include "rng.h"

static const uint64_t STATE[4] = {
    0xbdd732262feb6e95ULL, 0x28efe333b266f103ULL,
    0x47526757130f9f52ULL, 0x581ce1ff0e4ae394ULL};
static const uint64_t NEXT8[8] = {
    0x15780b2e0c2ec716ULL, 0x6104d9866d113a7eULL,
    0xae17533239e499a1ULL, 0xecb8ad4703b360a1ULL,
    0xfde6dc7fe2ec5e64ULL, 0xc50da53101795238ULL,
    0xb82154855a65ddb2ULL, 0xd99a2743ebe60087ULL};
static const double UNIFORM4[4] = {
    0.08386297105988216, 0.3789802506626686,
    0.6800434110281394, 0.9246929453253876};
static const double NORMAL4[4] = {
    -0.303263064678738, 1.3438117634372806,
    0.3834617912676943, 0.9369624250258953};

int main(void)
{
    tfs_rng r;
    int i;

    tfs_rng_seed(&r, 42);
    for (i = 0; i < 4; i++)
        CHECK(r.s[i] == STATE[i], "상태 s%d", i);
    for (i = 0; i < 8; i++)
        CHECK(tfs_rng_next(&r) == NEXT8[i], "next %d", i);

    tfs_rng_seed(&r, 42);
    for (i = 0; i < 4; i++)
        CHECK(tfs_rng_uniform(&r) == UNIFORM4[i], "uniform %d", i);

    tfs_rng_seed(&r, 42);
    for (i = 0; i < 4; i++) {
        double v = tfs_rng_normal(&r);
        CHECK(v == NORMAL4[i], "normal %d: %.17g", i, v);
    }

    {   /* randint 은 범위 안, permutation 은 순열 */
        int seen[7] = {0}, p[50], mark[50] = {0}, ok = 1;
        tfs_rng_seed(&r, 3);
        for (i = 0; i < 7000; i++) {
            int k = tfs_rng_randint(&r, 7);
            if (k < 0 || k >= 7)
                ok = 0;
            else
                seen[k]++;
        }
        CHECK(ok, "randint 범위");
        for (i = 0; i < 7; i++)
            CHECK(seen[i] > 800 && seen[i] < 1200, "randint 고르기");
        tfs_rng_seed(&r, 5);
        tfs_rng_permutation(&r, p, 50);
        for (i = 0; i < 50; i++)
            mark[p[i]]++;
        for (i = 0; i < 50; i++)
            CHECK(mark[i] == 1, "순열 %d", i);
    }
    return check_report("test_rng");
}
