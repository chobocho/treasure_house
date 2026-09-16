/* test_sample.c — KV 캐시로 한 토큰씩 늘린 로짓이 전체를 다시 계산한
 * 로짓과 같은가(위치 방식 셋), SPEC §7 거르개가 파이썬 시험과 같은
 * 답을 내는가, greedy 이어 쓰기가 파이썬과 토큰까지 같은가. */
#include <string.h>

#include "check.h"
#include "model.h"
#include "pool.h"
#include "sample.h"
#include "tfx.h"

static void cache_matches_full(const char *pos)
{
    char path[128];
    tfs_model m;
    tfs_kv kv;
    int ids[6] = {3, 7, 1, 10, 0, 5}, n, t, v;
    double worst = 0;

    snprintf(path, sizeof path, "ckpt/parity/tiny_%s.ckpt", pos);
    tfs_model_from_ckpt(&m, path);
    tfs_model_alloc(&m, 1, 6);
    tfs_forward(&m, ids, NULL, 1, 6);
    tfs_kv_init(&kv, &m);
    for (n = 0; n < 6; n++) {
        const float *row = tfs_kv_step(&kv, ids[n]);
        for (v = 0; v < m.c.V; v++) {
            double e = rel_err(row[v], m.a.logits[n * m.c.V + v]);
            if (e > worst)
                worst = e;
        }
    }
    CHECK(worst <= 1e-5, "%s 캐시 로짓 상대오차 %.3g", pos, worst);
    t = tfs_kv_step(&kv, 1) == NULL;
    CHECK(t, "%s 문맥을 넘기면 NULL", pos);
    tfs_kv_free(&kv);
    tfs_model_free(&m);
}

int main(void)
{
    tfs_pool_init(1);
    cache_matches_full("learned");
    cache_matches_full("sin");
    cache_matches_full("rope");

    {   /* top-p: 확률 0.1 0.4 0.3 0.2 */
        float lg[4];
        int ids[4], k, i;
        double pr[4], p[4] = {0.1, 0.4, 0.3, 0.2};
        for (i = 0; i < 4; i++)
            lg[i] = (float)log(p[i]);
        k = tfs_filtered(lg, 4, 1.0, 0, 0.7, ids, pr);
        CHECK(k == 2 && ids[0] == 1 && ids[1] == 2, "top-p 0.7");
        k = tfs_filtered(lg, 4, 1.0, 0, 0.71, ids, pr);
        CHECK(k == 3, "top-p 0.71 은 셋");
        k = tfs_filtered(lg, 4, 1.0, 2, 0.5, ids, pr);
        CHECK(k == 1 && ids[0] == 1, "top-k 2 뒤 다시 정규화한 top-p");
    }
    {   /* 동률은 작은 id, 온도 0 은 argmax */
        float lg[4] = {0, 1, 1, 0};
        int ids[4];
        double pr[4];
        tfs_rng r;
        tfs_rng_seed(&r, 1);
        CHECK(tfs_filtered(lg, 4, 1.0, 2, 1.0, ids, pr) == 2
                  && ids[0] == 1 && ids[1] == 2, "동률");
        CHECK(tfs_sample_next(lg, 4, 0.0, 0, 1.0, &r) == 1, "argmax");
    }
    {   /* greedy 이어 쓰기 — 파이썬 sample.generate 와 토큰까지 */
        tfx_file f = tfx_open("ckpt/parity/sample.tfx");
        int n, np, i, out[64], got, ok;
        double *want = tfx_get(f, "greedy", &n);
        double *prompt = tfx_get(f, "prompt", &np);
        int p[8];
        tfs_model m;
        for (i = 0; i < np; i++)
            p[i] = (int)prompt[i];
        tfs_model_from_ckpt(&m, "ckpt/parity/tiny_learned.ckpt");
        got = tfs_generate(&m, p, np, n - np, 0.0, 0, 1.0, 0, out);
        ok = got == n;
        for (i = 0; ok && i < n; i++)
            ok = out[i] == (int)want[i];
        CHECK(ok, "greedy 이어 쓰기가 파이썬과 같다 (길이 %d)", got);
        tfs_model_free(&m);
    }
    tfs_pool_free();
    return check_report("test_sample");
}
