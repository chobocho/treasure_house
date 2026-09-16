/* model.h — GPT 형 디코더의 순전파·역전파 (SPEC.md §3·§4). */
#ifndef TFS_MODEL_H
#define TFS_MODEL_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int V, T, d, L, h, d_ff;
    int pos;                  /* 0 learned · 1 sin · 2 rope */
} tfs_config;

/* 블록 하나의 활성값 — 역전파가 다시 읽는다 */
typedef struct {
    float *x_in, *ln1_xhat, *ln1_sinv, *ln1_out, *q, *k, *v, *att;
    float *att_out, *x_mid, *ln2_xhat, *ln2_sinv, *ln2_out;
    float *fc1, *fc1_act;
} tfs_block_acts;

/* 헤드 j 는 q·k·v·att_out 의 열 j·d_k ‥ 에 있다(SPEC §3.1). 파이썬은
 * (B, h, T, d_k) 로 축을 옮기지만 C 는 (B·T, d) 그대로 두고 열로
 * 읽는다. */
typedef struct {
    tfs_block_acts *h;
    float *x_out, *lnf_xhat, *lnf_sinv, *lnf_out, *logits, *probs;
    float *nll;                            /* 행마다 −log p[정답] */
    float *t3d, *td, *td2, *tff;           /* 순전파·역전파의 임시 */
    float *g3d, *gd, *gd2, *gff, *gV;
} tfs_acts;

typedef struct {
    tfs_config c;
    size_t n_params;
    float *params, *grads;
    int n_tensors;
    const char **names;       /* 체크포인트 차례의 이름 */
    size_t *offsets, *sizes;
    tfs_acts a;
    int B, T;                 /* 활성값을 잡아 둔 크기 */
} tfs_model;

size_t tfs_param_count(const tfs_config *c);
int tfs_model_init(tfs_model *m, const tfs_config *c, uint64_t seed);
int tfs_model_from_ckpt(tfs_model *m, const char *path);
int tfs_ckpt_save(const tfs_model *m, const char *path);
void tfs_model_alloc(tfs_model *m, int B, int T);
void tfs_model_free(tfs_model *m);
void tfs_zero_grad(tfs_model *m);
float *tfs_tensor(const tfs_model *m, float *base, int layer,
                  const char *name);
double tfs_forward(tfs_model *m, const int *ids, const int *targets,
                   int B, int T);
void tfs_backward(tfs_model *m, const int *ids, const int *targets,
                  int B, int T);

#endif
