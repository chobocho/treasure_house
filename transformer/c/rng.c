/* rng.c — splitmix64 로 씨앗을 펴고 xoshiro256** 로 뽑는다 (SPEC §1).
 *
 * C 의 uint64_t 는 2⁶⁴ 에서 넘치는 것이 규격이다. 파이썬이 & MASK 로
 * 흉내 내던 일을 여기서는 언어가 해 준다. 한 번 뽑기 O(1).
 */
#include <math.h>

#include "rng.h"

/* -std=c99 에는 M_PI 가 없다. 파이썬 math.pi 의 repr 과 같은 double. */
#define TFS_PI 3.141592653589793

static uint64_t rotl(uint64_t x, int k)
{
    return (x << k) | (x >> (64 - k));
}

void tfs_rng_seed(tfs_rng *r, uint64_t seed)
{
    uint64_t x = seed;
    int i;

    for (i = 0; i < 4; i++) {
        uint64_t z = (x += 0x9E3779B97F4A7C15ULL);
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        r->s[i] = z ^ (z >> 31);
    }
}

uint64_t tfs_rng_next(tfs_rng *r)
{
    uint64_t *s = r->s;
    uint64_t result = rotl(s[1] * 5, 7) * 9;
    uint64_t t = s[1] << 17;

    s[2] ^= s[0];
    s[3] ^= s[1];
    s[1] ^= s[2];
    s[0] ^= s[3];
    s[2] ^= t;
    s[3] = rotl(s[3], 45);
    return result;
}

/* [0, 1) — 위 53비트. 2⁻⁵³ 은 double 로 정확히 표현된다. */
double tfs_rng_uniform(tfs_rng *r)
{
    return (double)(tfs_rng_next(r) >> 11)
           * (1.0 / 9007199254740992.0);
}

/* Box–Muller 의 코사인 쪽만, 캐시 없이. u1 = 1 − uniform 은 (0, 1]. */
double tfs_rng_normal(tfs_rng *r)
{
    double u1 = 1.0 - tfs_rng_uniform(r);
    double u2 = tfs_rng_uniform(r);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * TFS_PI * u2);
}

int tfs_rng_randint(tfs_rng *r, int n)
{
    return (int)(tfs_rng_uniform(r) * n);
}

/* 피셔–예이츠, i = n−1 에서 1 까지. O(n). */
void tfs_rng_permutation(tfs_rng *r, int *p, int n)
{
    int i;

    for (i = 0; i < n; i++)
        p[i] = i;
    for (i = n - 1; i > 0; i--) {
        int j = tfs_rng_randint(r, i + 1);
        int t = p[i];
        p[i] = p[j];
        p[j] = t;
    }
}
