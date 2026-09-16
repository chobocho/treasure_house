/* test_model.c — 같은 체크포인트에서 C 의 로짓·손실·기울기가 파이썬
 * 참조와 맞는가(SPEC §9: 로짓 상대 1e-4, 기울기 1e-3). 위치 방식
 * 셋 모두. 그리고 스레드 1개와 3개의 기울기가 비트까지 같은가(§8). */
#include <string.h>

#include "check.h"
#include "model.h"
#include "pool.h"
#include "tfx.h"

static double worst(const float *got, const double *want, int n)
{
    double w = 0;
    int i;
    for (i = 0; i < n; i++) {
        double e = rel_err(got[i], want[i]);
        if (e > w)
            w = e;
    }
    return w;
}

/* SPEC §9 기울기 기준: 칸마다 |a−b| ≤ 1e-3·|b| + 1e-5·max|b|.
 * 기준을 넘는 칸 수를 돌려준다(0 이어야 한다). */
static int grad_misses(const float *got, const double *want, int n,
                       double *worst_ratio)
{
    double mx = 0, w = 0;
    int i, bad = 0;
    for (i = 0; i < n; i++)
        if (fabs(want[i]) > mx)
            mx = fabs(want[i]);
    for (i = 0; i < n; i++) {
        double lim = 1e-3 * fabs(want[i]) + 1e-5 * mx;
        double r = lim > 0 ? fabs(got[i] - want[i]) / lim : 0;
        if (r > w)
            w = r;
        bad += r > 1.0;
    }
    *worst_ratio = w;
    return bad;
}

static void run(const char *pos)
{
    char path[128];
    tfs_model m;
    tfx_file f;
    int n, nt, i, B = 2, T, ids[64], tg[64];
    double *x, *loss;
    float *grads1;

    snprintf(path, sizeof path, "ckpt/parity/tiny_%s.ckpt", pos);
    CHECK(tfs_model_from_ckpt(&m, path) == 0, "%s 를 못 읽는다", path);
    snprintf(path, sizeof path, "ckpt/parity/tiny_%s.tfx", pos);
    f = tfx_open(path);
    T = m.c.T;
    x = tfx_get(f, "ids", &n);
    for (i = 0; i < n; i++)
        ids[i] = (int)x[i];
    x = tfx_get(f, "targets", &nt);
    for (i = 0; i < nt; i++)
        tg[i] = (int)x[i];
    loss = tfx_get(f, "loss", &n);

    tfs_pool_init(1);
    tfs_model_alloc(&m, B, T);
    tfs_zero_grad(&m);
    {
        double l = tfs_forward(&m, ids, tg, B, T);
        tfs_backward(&m, ids, tg, B, T);
        CHECK(rel_err(l, loss[0]) <= 1e-4, "%s 손실 %.9g vs %.9g", pos,
              l, loss[0]);
    }
    x = tfx_get(f, "logits", &n);
    CHECK(n == B * T * m.c.V && worst(m.a.logits, x, n) <= 1e-4,
          "%s 로짓 %.3g", pos, worst(m.a.logits, x, n));

    for (i = 0; i < m.n_tensors; i++) {
        char name[64];
        double w;
        snprintf(name, sizeof name, "grad_%s", m.names[i]);
        x = tfx_get(f, name, &n);
        CHECK(x && (size_t)n == m.sizes[i], "%s %s 크기", pos, name);
        if (!x)
            continue;
        CHECK(grad_misses(m.grads + m.offsets[i], x, n, &w) == 0,
              "%s %s 기울기가 기준을 %.3g 배 넘는다", pos, name, w);
    }

    /* 스레드 셋 — 출력 칸마다 한 스레드가 정해진 차례로 계산하므로
     * 1 스레드와 비트까지 같아야 한다 */
    grads1 = malloc(sizeof(float) * m.n_params);
    memcpy(grads1, m.grads, sizeof(float) * m.n_params);
    tfs_pool_free();
    tfs_pool_init(3);
    tfs_zero_grad(&m);
    tfs_forward(&m, ids, tg, B, T);
    tfs_backward(&m, ids, tg, B, T);
    CHECK(memcmp(grads1, m.grads, sizeof(float) * m.n_params) == 0,
          "%s 스레드 1·3 기울기가 비트까지 같다", pos);
    tfs_pool_free();
    free(grads1);
    tfs_model_free(&m);
}

int main(void)
{
    tfs_config c = {50257, 1024, 768, 12, 12, 3072, 0};
    CHECK(tfs_param_count(&c) == 124439808UL, "GPT-2 small %lu",
          (unsigned long)tfs_param_count(&c));
    run("learned");
    run("sin");
    run("rope");
    return check_report("test_model");
}
