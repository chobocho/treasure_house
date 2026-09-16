/* train.h — AdamW·기울기 자르기·학습률 일정·배치 (SPEC.md §6). */
#ifndef TFS_TRAIN_H
#define TFS_TRAIN_H

#include "model.h"
#include "rng.h"

typedef struct {
    float *m, *v;
    int t;
} tfs_adamw;

typedef struct {
    int steps, B, warmup, newline;
    double lr_max, lr_min;
    uint64_t seed;
} tfs_train_cfg;

void tfs_adamw_init(tfs_adamw *o, size_t n);
void tfs_adamw_free(tfs_adamw *o);
void tfs_adamw_step(tfs_adamw *o, tfs_model *m, double lr, double wd);
double tfs_clip_grad_norm(tfs_model *m, double max_norm);
double tfs_lr_schedule(int t, double lr_max, double lr_min, int warmup,
                       int total);
int tfs_batch_starts(const int *tokens, int n, int T, int newline,
                     int *starts);
void tfs_get_batch(const int *tokens, const int *starts, int ns, int B,
                   int T, tfs_rng *r, int *x, int *y);
double tfs_train_step(tfs_model *m, tfs_adamw *o, const int *x,
                      const int *y, int B, double lr, double *norm);
int tfs_opt_save(const tfs_adamw *o, const tfs_model *m,
                 const char *path);
int tfs_opt_load(tfs_adamw *o, const tfs_model *m, const char *path);

#endif
