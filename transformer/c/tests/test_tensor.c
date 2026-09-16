/* test_tensor.c — 행렬곱 세 가지 루프 차례가 같은 답을 내는가, 그리고
 * 파이썬 참조(ckpt/parity/matmul.tfx)와 맞는가. PLAN.md §3.2 표 2행. */
#include "check.h"
#include "rng.h"
#include "tensor.h"
#include "tfx.h"

static double maxrel(const float *a, const float *b, int n)
{
    double m = 0;
    int i;
    for (i = 0; i < n; i++) {
        double e = rel_err(a[i], b[i]);
        if (e > m)
            m = e;
    }
    return m;
}

int main(void)
{
    int na, nb, nc, i;
    tfx_file f = tfx_open("ckpt/parity/matmul.tfx");
    double *A = tfx_get(f, "A", &na), *B = tfx_get(f, "B", &nb);
    double *C = tfx_get(f, "C", &nc);
    float *a = to_float(A, na), *b = to_float(B, nb);
    float c[21];

    CHECK(na == 35 && nb == 15 && nc == 21, "자료 모양");
    tfs_matmul_ikj(c, a, b, 7, 5, 3);
    for (i = 0; i < 21; i++)
        CHECK(rel_err(c[i], C[i]) <= 1e-5, "파이썬과 %d: %g vs %g", i,
              c[i], C[i]);

    {   /* 크고 모양이 어긋난 행렬에서 세 차례가 같은가 */
        int n = 67, m = 45, p = 53, blk;
        float *x = malloc(sizeof(float) * (size_t)(n * m));
        float *y = malloc(sizeof(float) * (size_t)(m * p));
        float *z1 = malloc(sizeof(float) * (size_t)(n * p));
        float *z2 = malloc(sizeof(float) * (size_t)(n * p));
        float *z3 = malloc(sizeof(float) * (size_t)(n * p));
        tfs_rng r;
        tfs_rng_seed(&r, 9);
        for (i = 0; i < n * m; i++)
            x[i] = (float)tfs_rng_normal(&r);
        for (i = 0; i < m * p; i++)
            y[i] = (float)tfs_rng_normal(&r);
        tfs_matmul_ijk(z1, x, y, n, m, p);
        tfs_matmul_ikj(z2, x, y, n, m, p);
        CHECK(maxrel(z1, z2, n * p) <= 1e-6, "ijk vs ikj %g",
              maxrel(z1, z2, n * p));
        /* 더하는 차례가 같아 사실은 비트까지 같다 (tensor.c 머리말) */
        CHECK(memcmp(z1, z2, sizeof(float) * (size_t)(n * p)) == 0,
              "ijk 와 ikj 가 비트까지 같다");
        for (blk = 1; blk <= 64; blk *= 4) {
            tfs_matmul_blocked(z3, x, y, n, m, p, blk);
            CHECK(maxrel(z2, z3, n * p) <= 1e-6, "블록 %d: %g", blk,
                  maxrel(z2, z3, n * p));
            CHECK(memcmp(z2, z3, sizeof(float) * (size_t)(n * p)) == 0,
                  "블록 %d 비트까지", blk);
        }
    }

    {   /* 전치와 편향 */
        float t[6] = {1, 2, 3, 4, 5, 6}, u[6], bias[3] = {10, 20, 30};
        tfs_transpose(u, t, 2, 3);
        CHECK(u[0] == 1 && u[1] == 4 && u[2] == 2 && u[5] == 6, "전치");
        tfs_add_bias(t, bias, 2, 3);
        CHECK(t[0] == 11 && t[4] == 25 && t[5] == 36, "편향");
    }
    return check_report("test_tensor");
}
