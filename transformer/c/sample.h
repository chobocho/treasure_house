/* sample.h — KV 캐시 추론과 SPEC.md §7 의 뽑기. */
#ifndef TFS_SAMPLE_H
#define TFS_SAMPLE_H

#include "model.h"
#include "rng.h"

typedef struct {
    const tfs_model *m;
    float *k, *v;              /* [L · T · d] — 블록·위치마다 */
    int n;                     /* 캐시에 든 위치 수 */
    float *x, *a, *xhat, *qkv, *att, *z, *o, *f, *logits;
} tfs_kv;

void tfs_kv_init(tfs_kv *kv, const tfs_model *m);
void tfs_kv_free(tfs_kv *kv);
void tfs_kv_reset(tfs_kv *kv);
const float *tfs_kv_step(tfs_kv *kv, int token);
int tfs_filtered(const float *logits, int V, double temp, int top_k,
                 double top_p, int *ids, double *probs);
int tfs_sample_next(const float *logits, int V, double temp, int top_k,
                    double top_p, tfs_rng *r);
int tfs_generate(const tfs_model *m, const int *prompt, int np,
                 int n_new, double temp, int top_k, double top_p,
                 uint64_t seed, int *out);

#endif
