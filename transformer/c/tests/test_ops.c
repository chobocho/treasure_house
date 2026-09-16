/* test_ops.c — 부품 커널을 파이썬 참조(ckpt/parity/ops.tfx)와 견준다.
 * 허용 오차는 SPEC §9: 순전파 상대 1e-4, 역전파 상대 1e-3. */
#include "check.h"
#include "ops.h"
#include "tfx.h"

#define FWD 1e-4
#define BWD 1e-3

static tfx_file F;

static double *get(const char *name, int *n)
{
    double *x = tfx_get(F, name, n);
    if (!x) {
        printf("  ✗ 자료에 %s 가 없다\n", name);
        exit(2);
    }
    return x;
}

static void compare(const char *what, const float *got,
                    const double *want, int n, double tol)
{
    double worst = 0;
    int i;
    for (i = 0; i < n; i++) {
        double e = rel_err(got[i], want[i]);
        if (e > worst)
            worst = e;
    }
    CHECK(worst <= tol, "%s: 최대 상대오차 %.3g > %.0e", what, worst,
          tol);
}

int main(void)
{
    int n, i;
    F = tfx_open("ckpt/parity/ops.tfx");

    {   /* 소프트맥스 — 로짓이 커서 max 를 빼지 않으면 넘친다 */
        double *x = get("softmax_x", &n), *y = get("softmax_y", &n);
        float *xf = to_float(x, n), out[18];
        for (i = 0; i < 3; i++)
            tfs_softmax_row(out + 6 * i, xf + 6 * i, 6);
        compare("softmax", out, y, 18, FWD);
    }
    {   /* 교차엔트로피: 손실과 (p − y)/N */
        int nt;
        double *z = get("ce_z", &n), *t = get("ce_t", &nt);
        double *loss = get("ce_loss", &nt), *dz = get("ce_dz", &nt);
        float *zf = to_float(z, n), p[36], g[36] = {0};
        double total = 0;
        for (i = 0; i < 4; i++)
            total += tfs_cross_entropy_row(p + 9 * i, zf + 9 * i, 9,
                                           (int)t[i]);
        CHECK(rel_err(total / 4, loss[0]) <= FWD,
              "CE 손실 %.9g vs %.9g", total / 4, loss[0]);
        for (i = 0; i < 4; i++)
            tfs_cross_entropy_backward_row(g + 9 * i, p + 9 * i, 9,
                                           (int)t[i], 0.25f);
        compare("CE 기울기", g, dz, 36, BWD);
    }
    {   /* 레이어놈 */
        int k;
        float *x = to_float(get("ln_x", &n), 24);
        float *gm = to_float(get("ln_g", &k), 8);
        float *bt = to_float(get("ln_b", &k), 8);
        float *dy = to_float(get("ln_dy", &k), 24);
        float y[24], xhat[24], sinv[3], dx[24] = {0}, dg[8] = {0};
        float db[8] = {0};
        tfs_layernorm_forward(y, xhat, sinv, x, gm, bt, 3, 8);
        compare("layernorm y", y, get("ln_y", &k), 24, FWD);
        tfs_layernorm_backward(dx, dg, db, dy, xhat, sinv, gm, 3, 8);
        compare("layernorm dx", dx, get("ln_dx", &k), 24, BWD);
        compare("layernorm dg", dg, get("ln_dg", &k), 8, BWD);
        compare("layernorm db", db, get("ln_db", &k), 8, BWD);
    }
    {   /* GELU */
        int k;
        float *x = to_float(get("gelu_x", &n), 20);
        float *dy = to_float(get("gelu_dy", &k), 20);
        float y[20], dx[20] = {0};
        tfs_gelu_forward(y, x, 20);
        compare("gelu y", y, get("gelu_y", &k), 20, FWD);
        tfs_gelu_backward(dx, x, dy, 20);
        compare("gelu dx", dx, get("gelu_dx", &k), 20, BWD);
        {
            float zero = 0, one = 1, d0 = 0;
            tfs_gelu_backward(&d0, &zero, &one, 1);
            CHECK(d0 == 0.5f, "gelu'(0) = %g", d0);
        }
    }
    {   /* 인과 소프트맥스 — i 행은 0‥i 칸만 */
        int k, b, r;
        float *s = to_float(get("cs_x", &n), 50);
        float *dy = to_float(get("cs_dy", &k), 50);
        float y[50] = {0}, dx[50] = {0};
        for (b = 0; b < 2; b++)
            for (r = 0; r < 5; r++) {
                int o = b * 25 + r * 5;
                tfs_softmax_row(y + o, s + o, r + 1);
                tfs_softmax_row_backward(dx + o, y + o, dy + o, r + 1);
            }
        compare("causal y", y, get("cs_y", &k), 50, FWD);
        compare("causal dx", dx, get("cs_dx", &k), 50, BWD);
    }
    return check_report("test_ops");
}
