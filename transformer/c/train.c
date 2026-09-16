/* train.c — 학습 한 걸음 (py/transformerlib/train.py·optim.py 의 C 판).
 *
 *   배치(SPEC §6.1) → 순전파·역전파 → 자르기(§6.3) → AdamW(§6.2)
 *
 * AdamW 는 파라미터 배열 하나를 도는 루프 하나다. 원소마다 m·v 를
 * 더 들고 다니므로 메모리는 파라미터의 3배. 원소 하나의 계산은 double
 * 로 하고 결과만 float32 로 담는다 — 파이썬과 같은 식을 같은 차례로.
 * 이 루프는 원소끼리 서로 기대지 않아 나눠도 되지만, 합을 쌓지 않으니
 * 스레드 수와 무관하게 같은 값이 나온다(여기서는 한 스레드로 돈다).
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "train.h"

#define TFS_PI 3.141592653589793

void tfs_adamw_init(tfs_adamw *o, size_t n)
{
    o->m = calloc(n, sizeof(float));
    o->v = calloc(n, sizeof(float));
    o->t = 0;
}

void tfs_adamw_free(tfs_adamw *o)
{
    free(o->m);
    free(o->v);
}

/* SPEC §6.2 — 행렬만 감쇠한다 */
static int decays(const char *name)
{
    const char *dot = strchr(name, '.');
    const char *nm = dot ? dot + 1 : name;
    return !strcmp(nm, "wte") || !strcmp(nm, "wpe")
           || !strcmp(nm, "Wqkv") || !strcmp(nm, "Wo")
           || !strcmp(nm, "W1") || !strcmp(nm, "W2");
}

void tfs_adamw_step(tfs_adamw *o, tfs_model *m, double lr, double wd)
{
    const double b1 = 0.9, b2 = 0.95, eps = 1e-8;
    double c1, c2;
    int i;

    o->t++;
    c1 = 1.0 - pow(b1, o->t);
    c2 = 1.0 - pow(b2, o->t);
    for (i = 0; i < m->n_tensors; i++) {
        size_t j, off = m->offsets[i], n = m->sizes[i];
        double w = decays(m->names[i]) ? wd : 0.0;
        for (j = off; j < off + n; j++) {
            double g = m->grads[j], th = m->params[j];
            double mm = b1 * o->m[j] + (1.0 - b1) * g;
            double vv = b2 * o->v[j] + (1.0 - b2) * g * g;
            double upd = (mm / c1) / (sqrt(vv / c2) + eps);
            o->m[j] = (float)mm;
            o->v[j] = (float)vv;
            m->params[j] = (float)(th - lr * (upd + w * th));
        }
    }
}

double tfs_clip_grad_norm(tfs_model *m, double max_norm)
{
    double sq = 0.0, n;
    size_t j;

    for (j = 0; j < m->n_params; j++)
        sq += (double)m->grads[j] * m->grads[j];
    n = sqrt(sq);
    if (n > max_norm) {
        double s = max_norm / (n + 1e-6);
        for (j = 0; j < m->n_params; j++)
            m->grads[j] = (float)(m->grads[j] * s);
    }
    return n;
}

/* SPEC §6.4. 식의 차례까지 파이썬 optim.lr_schedule 과 같게 적었다 —
 * 시험이 두 언어의 학습률을 == 로 견준다. */
double tfs_lr_schedule(int t, double lr_max, double lr_min, int warmup,
                       int total)
{
    double p, cs;
    int span = total - warmup > 1 ? total - warmup : 1;
    if (t <= warmup)
        return lr_max * t / warmup;
    p = (double)(t - warmup) / span;
    cs = 1.0 + cos(TFS_PI * p);
    return lr_min + 0.5 * (lr_max - lr_min) * cs;
}

int tfs_batch_starts(const int *tokens, int n, int T, int newline,
                     int *starts)
{
    int i, k = 0, last = n - T - 1;
    for (i = 0; i <= last; i++)
        if (newline < 0 || i == 0 || tokens[i - 1] == newline)
            starts[k++] = i;
    return k;
}

void tfs_get_batch(const int *tokens, const int *starts, int ns, int B,
                   int T, tfs_rng *r, int *x, int *y)
{
    int b, t;
    for (b = 0; b < B; b++) {
        int s = starts[tfs_rng_randint(r, ns)];
        for (t = 0; t < T; t++) {
            x[b * T + t] = tokens[s + t];
            y[b * T + t] = tokens[s + t + 1];
        }
    }
}

double tfs_train_step(tfs_model *m, tfs_adamw *o, const int *x,
                      const int *y, int B, double lr, double *norm)
{
    int T = m->c.T;
    double loss;
    tfs_zero_grad(m);
    loss = tfs_forward(m, x, y, B, T);
    tfs_backward(m, x, y, B, T);
    *norm = tfs_clip_grad_norm(m, 1.0);
    tfs_adamw_step(o, m, lr, 0.1);
    return loss;
}

/* SPEC §4.2 — "TFO1", int32 스텝, m 전체, v 전체 */
int tfs_opt_save(const tfs_adamw *o, const tfs_model *m,
                 const char *path)
{
    FILE *fp = fopen(path, "wb");
    int ok;
    if (!fp)
        return -1;
    ok = fwrite("TFO1", 1, 4, fp) == 4
         && fwrite(&o->t, sizeof(int), 1, fp) == 1
         && fwrite(o->m, sizeof(float), m->n_params, fp) == m->n_params
         && fwrite(o->v, sizeof(float), m->n_params, fp) == m->n_params;
    return (fclose(fp) == 0 && ok) ? 0 : -1;
}

int tfs_opt_load(tfs_adamw *o, const tfs_model *m, const char *path)
{
    FILE *fp = fopen(path, "rb");
    char magic[4];
    int ok;
    if (!fp)
        return -1;
    ok = fread(magic, 1, 4, fp) == 4 && memcmp(magic, "TFO1", 4) == 0
         && fread(&o->t, sizeof(int), 1, fp) == 1
         && fread(o->m, sizeof(float), m->n_params, fp) == m->n_params
         && fread(o->v, sizeof(float), m->n_params, fp) == m->n_params;
    fclose(fp);
    return ok ? 0 : -1;
}
