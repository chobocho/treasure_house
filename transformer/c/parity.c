/* parity.c — `tfs parity`: 파이썬(float64)과 C(float32)를 같은 입력에서
 * 나란히 놓고 차이를 표로 찍는다. 시험(c/tests/)은 통과·실패만 말하고,
 * 이 명령은 **얼마나** 가까운지를 말한다 — 9부가 그 표를 싣는다.
 *
 * 기준은 SPEC §9 그대로다. 기울기 칸의 "기준 대비" 는
 * |a−b| / (1e-3·|b| + 1e-5·max|b|) 의 최댓값이라 1 아래면 통과다.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "model.h"
#include "parity.h"
#include "pool.h"
#include "rng.h"
#include "sample.h"
#include "tfx.h"
#include "train.h"

static double max_rel(const float *a, const double *b, int n)
{
    double w = 0;
    int i;
    for (i = 0; i < n; i++) {
        double s = fabs(a[i]) > fabs(b[i]) ? fabs(a[i]) : fabs(b[i]);
        double e = fabs(a[i] - b[i]) / (s > 1e-6 ? s : 1e-6);
        if (e > w)
            w = e;
    }
    return w;
}

static double grad_ratio(const float *a, const double *b, int n)
{
    double mx = 0, w = 0;
    int i;
    for (i = 0; i < n; i++)
        if (fabs(b[i]) > mx)
            mx = fabs(b[i]);
    for (i = 0; i < n; i++) {
        double lim = 1e-3 * fabs(b[i]) + 1e-5 * mx;
        double r = lim > 0 ? fabs(a[i] - b[i]) / lim : 0;
        if (r > w)
            w = r;
    }
    return w;
}

static void model_section(const char *pos, int threads, int with_grads)
{
    char path[128];
    tfs_model m;
    tfx_file f;
    int n, i, ids[64], tg[64];
    double *x, loss;

    snprintf(path, sizeof path, "ckpt/parity/tiny_%s.ckpt", pos);
    tfs_model_from_ckpt(&m, path);
    snprintf(path, sizeof path, "ckpt/parity/tiny_%s.tfx", pos);
    f = tfx_open(path);
    x = tfx_get(f, "ids", &n);
    for (i = 0; i < n; i++)
        ids[i] = (int)x[i];
    x = tfx_get(f, "targets", &n);
    for (i = 0; i < n; i++)
        tg[i] = (int)x[i];
    tfs_pool_init(threads);
    tfs_model_alloc(&m, 2, m.c.T);
    tfs_zero_grad(&m);
    loss = tfs_forward(&m, ids, tg, 2, m.c.T);
    tfs_backward(&m, ids, tg, 2, m.c.T);
    if (!with_grads) {
        x = tfx_get(f, "loss", &n);
        printf("%-8s 손실 파이썬 %.9f · C %.9f · 차 %.1e\n", pos, x[0],
               loss, fabs(loss - x[0]));
        x = tfx_get(f, "logits", &n);
        printf("%-8s 로짓 %d칸 최대 상대 오차 %.1e (기준 1e-4)\n", pos,
               n, max_rel(m.a.logits, x, n));
    } else {
        /* 한글 머리말은 printf 폭이 바이트로 세므로 손으로 맞춘다 */
        printf("텐서               칸  기준 대비 (1 아래면 통과)\n");
        for (i = 0; i < m.n_tensors; i++) {
            char nm[64];
            snprintf(nm, sizeof nm, "grad_%s", m.names[i]);
            x = tfx_get(f, nm, &n);
            printf("%-14s %6d  %.3f\n", m.names[i], n,
                   grad_ratio(m.grads + m.offsets[i], x, n));
        }
    }
    tfs_pool_free();
    tfs_model_free(&m);
}

static void train_section(int threads)
{
    tfx_file f = tfx_open("ckpt/parity/train.tfx");
    int n, ntok, i, ns, t;
    double *c = tfx_get(f, "config", &n), *run = tfx_get(f, "run", &n);
    double *tk = tfx_get(f, "tokens", &ntok), *want;
    tfs_config cfg;
    tfs_model m;
    tfs_adamw o;
    tfs_rng r;
    int *tok = malloc(sizeof(int) * (size_t)ntok);
    int *starts, x[64], y[64];

    want = tfx_get(f, "loss", &n);
    for (i = 0; i < ntok; i++)
        tok[i] = (int)tk[i];
    cfg.V = (int)c[0], cfg.T = (int)c[1], cfg.d = (int)c[2];
    cfg.L = (int)c[3], cfg.h = (int)c[4], cfg.d_ff = (int)c[5];
    cfg.pos = 0;
    tfs_pool_init(threads);
    tfs_model_init(&m, &cfg, (uint64_t)run[4]);
    tfs_model_alloc(&m, (int)run[1], cfg.T);
    tfs_adamw_init(&o, m.n_params);
    starts = malloc(sizeof(int) * (size_t)ntok);
    ns = tfs_batch_starts(tok, ntok, cfg.T, (int)run[5], starts);
    tfs_rng_seed(&r, (uint64_t)run[4] + 1);
    printf("스텝   파이썬 손실        C 손실         차\n");
    for (t = 1; t <= (int)run[0]; t++) {
        double lr = tfs_lr_schedule(t, run[2], run[2] / 10, (int)run[3],
                                    (int)run[0]), norm, l;
        tfs_get_batch(tok, starts, ns, (int)run[1], cfg.T, &r, x, y);
        l = tfs_train_step(&m, &o, x, y, (int)run[1], lr, &norm);
        if (t <= 3 || t % 5 == 0)
            printf("%4d  %12.6f  %12.6f  %9.1e\n", t, want[t - 1], l,
                   fabs(l - want[t - 1]));
    }
    tfs_pool_free();
    free(tok), free(starts);
}

static void sample_section(void)
{
    tfx_file f = tfx_open("ckpt/parity/sample.tfx");
    int n, np, i, p[8], out[64], same = 1;
    double *want = tfx_get(f, "greedy", &n);
    double *prompt = tfx_get(f, "prompt", &np);
    tfs_model m;
    for (i = 0; i < np; i++)
        p[i] = (int)prompt[i];
    tfs_model_from_ckpt(&m, "ckpt/parity/tiny_learned.ckpt");
    tfs_pool_init(1);
    tfs_generate(&m, p, np, n - np, 0.0, 0, 0.0, 0, out);
    printf("파이썬:");
    for (i = 0; i < n; i++)
        printf(" %d", (int)want[i]);
    printf("\nC     :");
    for (i = 0; i < n; i++) {
        printf(" %d", out[i]);
        same &= out[i] == (int)want[i];
    }
    printf("\n%s\n", same ? "토큰까지 같다" : "다르다");
    tfs_pool_free();
    tfs_model_free(&m);
}

int tfs_parity_main(int threads)
{
    printf("== 1. 로짓과 손실 — 위치 방식 셋 ==\n");
    model_section("learned", threads, 0);
    model_section("sin", threads, 0);
    model_section("rope", threads, 0);
    printf("\n== 2. 기울기 — learned, 텐서마다 ==\n");
    model_section("learned", threads, 1);
    printf("\n== 3. 같은 씨앗으로 20 스텝 학습 ==\n");
    train_section(threads);
    printf("\n== 4. greedy 이어 쓰기 ==\n");
    sample_section();
    return 0;
}
