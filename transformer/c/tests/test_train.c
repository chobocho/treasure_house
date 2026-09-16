/* test_train.c — 같은 씨앗으로 20 스텝 학습한 손실이 파이썬과 절대
 * 1e-3 안인가(SPEC §9), 학습률 일정이 같은 double 을 내는가, 스레드
 * 1개와 4개의 체크포인트가 바이트까지 같은가(SPEC §8), .opt 가 읽고
 * 쓰기에서 같은가. PLAN.md §3.2 표 6행. */
#include <string.h>

#include "check.h"
#include "model.h"
#include "pool.h"
#include "rng.h"
#include "tfx.h"
#include "train.h"

static tfs_config cfg;
static tfs_train_cfg tc;
static int *tokens, ntok;

/* 새 모델을 씨앗에서 만들어 steps 스텝 학습하고 손실을 담는다. */
static void train(tfs_model *m, tfs_adamw *opt, int threads, int steps,
                  double *losses)
{
    tfs_pool_init(threads);
    tfs_model_init(m, &cfg, tc.seed);
    tfs_model_alloc(m, tc.B, cfg.T);
    tfs_adamw_init(opt, m->n_params);
    {
        int *starts = malloc(sizeof(int) * (size_t)ntok);
        int ns = tfs_batch_starts(tokens, ntok, cfg.T, tc.newline,
                                  starts);
        int *x = malloc(sizeof(int) * (size_t)(tc.B * cfg.T));
        int *y = malloc(sizeof(int) * (size_t)(tc.B * cfg.T));
        tfs_rng r;
        int t;
        tfs_rng_seed(&r, tc.seed + 1);
        for (t = 1; t <= steps; t++) {
            double lr = tfs_lr_schedule(t, tc.lr_max, tc.lr_min,
                                        tc.warmup, tc.steps);
            double norm;
            tfs_get_batch(tokens, starts, ns, tc.B, cfg.T, &r, x, y);
            losses[t - 1] = tfs_train_step(m, opt, x, y, tc.B, lr,
                                           &norm);
        }
        free(starts), free(x), free(y);
    }
    tfs_pool_free();
}

int main(void)
{
    tfx_file f = tfx_open("ckpt/parity/train.tfx");
    int n, i;
    double *c = tfx_get(f, "config", &n), *run = tfx_get(f, "run", &n);
    double *tk = tfx_get(f, "tokens", &ntok);
    double *want = tfx_get(f, "loss", &n), *lrs = tfx_get(f, "lr", &n);
    double losses[64], again[64];
    tfs_model m, m4;
    tfs_adamw opt, opt4;

    cfg.V = (int)c[0], cfg.T = (int)c[1], cfg.d = (int)c[2];
    cfg.L = (int)c[3], cfg.h = (int)c[4], cfg.d_ff = (int)c[5];
    cfg.pos = 0;
    tc.steps = (int)run[0], tc.B = (int)run[1], tc.lr_max = run[2];
    tc.lr_min = run[2] / 10.0, tc.warmup = (int)run[3];
    tc.seed = (uint64_t)run[4], tc.newline = (int)run[5];
    tokens = malloc(sizeof(int) * (size_t)ntok);
    for (i = 0; i < ntok; i++)
        tokens[i] = (int)tk[i];

    for (i = 1; i <= tc.steps; i++)
        CHECK(tfs_lr_schedule(i, tc.lr_max, tc.lr_min, tc.warmup,
                              tc.steps) == lrs[i - 1],
              "학습률 %d 스텝", i);

    train(&m, &opt, 1, tc.steps, losses);
    for (i = 0; i < tc.steps; i++)
        CHECK(fabs(losses[i] - want[i]) <= 1e-3,
              "스텝 %d 손실 %.6f vs 파이썬 %.6f", i + 1, losses[i],
              want[i]);
    CHECK(losses[tc.steps - 1] < losses[0], "손실이 준다");

    train(&m4, &opt4, 4, tc.steps, again);
    CHECK(memcmp(m.params, m4.params, sizeof(float) * m.n_params) == 0,
          "스레드 1·4 의 가중치가 바이트까지 같다");
    CHECK(memcmp(losses, again, sizeof(double) * (size_t)tc.steps) == 0,
          "스레드 1·4 의 손실 기록이 같다");

    CHECK(tfs_opt_save(&opt, &m, ".build/t.opt") == 0, ".opt 쓰기");
    {
        tfs_adamw o2;
        FILE *a, *b;
        char ba[1 << 16], bb[1 << 16];
        size_t na, nb;
        tfs_adamw_init(&o2, m.n_params);
        CHECK(tfs_opt_load(&o2, &m, ".build/t.opt") == 0, ".opt 읽기");
        CHECK(o2.t == tc.steps, ".opt 스텝 %d", o2.t);
        tfs_opt_save(&o2, &m, ".build/t2.opt");
        a = fopen(".build/t.opt", "rb");
        b = fopen(".build/t2.opt", "rb");
        na = fread(ba, 1, sizeof ba, a);
        nb = fread(bb, 1, sizeof bb, b);
        CHECK(na == nb && memcmp(ba, bb, na) == 0, ".opt 왕복");
        fclose(a), fclose(b);
    }
    {   /* 기울기가 0 이면 감쇠만 — θ 가 정확히 (1 − lr·wd) 배 */
        float before = tfs_tensor(&m, m.params, 0, "W1")[0];
        float bias = tfs_tensor(&m, m.params, 0, "b1")[0];
        tfs_zero_grad(&m);
        memset(opt.m, 0, sizeof(float) * m.n_params);
        memset(opt.v, 0, sizeof(float) * m.n_params);
        tfs_adamw_step(&opt, &m, 0.5, 0.1);
        CHECK(tfs_tensor(&m, m.params, 0, "W1")[0]
                  == (float)(before * (1 - 0.5 * 0.1)),
              "AdamW 감쇠");
        CHECK(tfs_tensor(&m, m.params, 0, "b1")[0] == bias,
              "편향은 감쇠하지 않는다");
    }
    return check_report("test_train");
}
