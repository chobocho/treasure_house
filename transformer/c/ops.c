/* ops.c — 트랜스포머 부품의 순전파·역전파 (py/transformerlib/ops.py).
 *
 * 값은 float32 로 들고, 행 하나의 합(소프트맥스 분모, 평균·분산,
 * 내적)만 double 로 쌓는다. 합은 수백 개를 더하므로 float32 로 쌓으면
 * 반올림이 쌓여 파이썬(fsum)과 멀어진다. 원소 하나는 float32 로 충분.
 * 모든 함수가 한 행(또는 원소)에 대해 O(n) 시간, 추가 공간 O(1).
 */
#include <math.h>

#include "ops.h"

/* p = softmax(z). 최댓값을 먼저 빼 exp 가 넘치지 않게 한다. */
void tfs_softmax_row(float *p, const float *z, int n)
{
    double m = z[0], s = 0.0;
    int j;

    for (j = 1; j < n; j++)
        if (z[j] > m)
            m = z[j];
    for (j = 0; j < n; j++)
        s += exp((double)z[j] - m);
    for (j = 0; j < n; j++)
        p[j] = (float)(exp((double)z[j] - m) / s);
}

/* dz += p ⊙ (dp − ⟨dp, p⟩) — 야코비안 diag(p) − ppᵀ 를 곱한 것. */
void tfs_softmax_row_backward(float *dz, const float *p,
                              const float *dp, int n)
{
    double dot = 0.0;
    int j;

    for (j = 0; j < n; j++)
        dot += (double)dp[j] * p[j];
    for (j = 0; j < n; j++)
        dz[j] += (float)(p[j] * ((double)dp[j] - dot));
}

/* −log p[target] 을 로그합지수로 돌려주고 p 를 채운다. */
double tfs_cross_entropy_row(float *p, const float *z, int n,
                             int target)
{
    double m = z[0], s = 0.0;
    int j;

    for (j = 1; j < n; j++)
        if (z[j] > m)
            m = z[j];
    for (j = 0; j < n; j++)
        s += exp((double)z[j] - m);
    for (j = 0; j < n; j++)
        p[j] = (float)(exp((double)z[j] - m) / s);
    return m + log(s) - z[target];
}

/* dz += (p − y)·scale. scale 은 윗기울기 / 행 수 (평균이므로). */
void tfs_cross_entropy_backward_row(float *dz, const float *p, int n,
                                    int target, float scale)
{
    int j;

    for (j = 0; j < n; j++)
        dz[j] += (p[j] - (j == target ? 1.0f : 0.0f)) * scale;
}

void tfs_layernorm_forward(float *y, float *xhat, float *sinv,
                           const float *x, const float *g,
                           const float *b, int rows, int n)
{
    int r, j;

    for (r = 0; r < rows; r++) {
        const float *xr = x + r * n;
        double mu = 0.0, var = 0.0, s;
        for (j = 0; j < n; j++)
            mu += xr[j];
        mu /= n;
        for (j = 0; j < n; j++)
            var += (xr[j] - mu) * (xr[j] - mu);
        var /= n;
        s = 1.0 / sqrt(var + TFS_LN_EPS);
        sinv[r] = (float)s;
        for (j = 0; j < n; j++) {
            double xh = (xr[j] - mu) * s;
            xhat[r * n + j] = (float)xh;
            y[r * n + j] = (float)(g[j] * xh + b[j]);
        }
    }
}

/* d = dy ⊙ g 라 두면 dx = (d − mean d − x̂·mean(d ⊙ x̂)) / σ.
 * 유도는 4부. μ·σ 가 행 전체에 기대므로 칸끼리 섞이는 두 항이
 * 붙는다. */
void tfs_layernorm_backward(float *dx, float *dg, float *db,
                            const float *dy, const float *xhat,
                            const float *sinv, const float *g, int rows,
                            int n)
{
    int r, j;

    for (r = 0; r < rows; r++) {
        const float *dyr = dy + r * n, *xh = xhat + r * n;
        double md = 0.0, mdx = 0.0;
        for (j = 0; j < n; j++) {
            double d = (double)dyr[j] * g[j];
            md += d;
            mdx += d * xh[j];
        }
        md /= n;
        mdx /= n;
        for (j = 0; j < n; j++) {
            double d = (double)dyr[j] * g[j];
            dx[r * n + j] += (float)((d - md - xh[j] * mdx) * sinv[r]);
            dg[j] += dyr[j] * xh[j];
            db[j] += dyr[j];
        }
    }
}

/* GELU tanh 근사 — ½x(1 + tanh(A(x + Bx³))). 상수는 SPEC §3.3. */
void tfs_gelu_forward(float *y, const float *x, int n)
{
    int i;

    for (i = 0; i < n; i++) {
        double v = x[i];
        double t = tanh(TFS_GELU_A * (v + TFS_GELU_B * v * v * v));
        y[i] = (float)(0.5 * v * (1.0 + t));
    }
}

/* ½(1 + t) + ½x(1 − t²)·A(1 + 3Bx²). x = 0 이면 정확히 ½. */
void tfs_gelu_backward(float *dx, const float *x, const float *dy,
                       int n)
{
    int i;

    for (i = 0; i < n; i++) {
        double v = x[i];
        double t = tanh(TFS_GELU_A * (v + TFS_GELU_B * v * v * v));
        double d = 0.5 * (1.0 + t)
                   + 0.5 * v * (1.0 - t * t) * TFS_GELU_A
                     * (1.0 + 3.0 * TFS_GELU_B * v * v);
        dx[i] += (float)(d * dy[i]);
    }
}
