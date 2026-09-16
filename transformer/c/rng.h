/* rng.h — SPEC.md §1 의 난수. py/transformerlib/rng.py 와 같은 수열. */
#ifndef TFS_RNG_H
#define TFS_RNG_H

#include <stdint.h>

typedef struct {
    uint64_t s[4];
} tfs_rng;

void tfs_rng_seed(tfs_rng *r, uint64_t seed);
uint64_t tfs_rng_next(tfs_rng *r);
double tfs_rng_uniform(tfs_rng *r);
double tfs_rng_normal(tfs_rng *r);
int tfs_rng_randint(tfs_rng *r, int n);
void tfs_rng_permutation(tfs_rng *r, int *p, int n);

#endif
