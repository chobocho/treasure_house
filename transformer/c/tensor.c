/* tensor.c — float32 평면 버퍼의 기본 연산.
 *
 * 행렬곱을 세 번 짠다. 계산은 같고 **메모리를 읽는 차례**만 다르다.
 *
 *   ijk      out[i][j] = Σ_k a[i][k]·b[k][j]   — 교과서 차례.
 *            안쪽 루프가 b 를 **열 방향**으로 훑어 캐시를 자주 놓친다.
 *   ikj      a[i][k] 하나를 잡고 b 의 k 행을 **앞에서부터** 읽는다.
 *            파이썬 참조(tensor.matmul)와 같은 차례다.
 *   blocked  ikj 를 block×block 조각으로 나눠 조각이 캐시에 들게 한다.
 *
 * 세 차례 모두 (i, j) 칸에 k 를 **작은 것부터** 더하므로 부동소수
 * 결과는 비트까지 같다. 9부의 벤치 표는 같은 답을 내는 데 드는 시간만
 * 견준다. 시간 O(n·m·p), 추가 공간 O(1).
 */
#include <string.h>

#include "tensor.h"

void tfs_matmul_ijk(float *out, const float *a, const float *b, int n,
                    int m, int p)
{
    int i, j, k;

    for (i = 0; i < n; i++)
        for (j = 0; j < p; j++) {
            float s = 0.0f;
            for (k = 0; k < m; k++)
                s += a[i * m + k] * b[k * p + j];
            out[i * p + j] = s;
        }
}

void tfs_matmul_ikj(float *out, const float *a, const float *b, int n,
                    int m, int p)
{
    int i, j, k;

    memset(out, 0, sizeof(float) * (size_t)(n * p));
    for (i = 0; i < n; i++) {
        float *o = out + i * p;
        for (k = 0; k < m; k++) {
            float aik = a[i * m + k];
            const float *bk = b + k * p;
            for (j = 0; j < p; j++)
                o[j] += aik * bk[j];
        }
    }
}

static int min_int(int x, int y)
{
    return x < y ? x : y;
}

void tfs_matmul_blocked(float *out, const float *a, const float *b,
                        int n, int m, int p, int block)
{
    int i0, k0, j0, i, j, k;

    memset(out, 0, sizeof(float) * (size_t)(n * p));
    for (i0 = 0; i0 < n; i0 += block)
        for (k0 = 0; k0 < m; k0 += block)
            for (j0 = 0; j0 < p; j0 += block)
                for (i = i0; i < min_int(i0 + block, n); i++)
                    for (k = k0; k < min_int(k0 + block, m); k++) {
                        float aik = a[i * m + k];
                        int jend = min_int(j0 + block, p);
                        for (j = j0; j < jend; j++)
                            out[i * p + j] += aik * b[k * p + j];
                    }
}

void tfs_transpose(float *out, const float *a, int n, int m)
{
    int i, j;

    for (i = 0; i < n; i++)
        for (j = 0; j < m; j++)
            out[j * n + i] = a[i * m + j];
}

void tfs_add_bias(float *x, const float *b, int rows, int cols)
{
    int r, c;

    for (r = 0; r < rows; r++)
        for (c = 0; c < cols; c++)
            x[r * cols + c] += b[c];
}
