/* sample.c — KV 캐시 추론과 뽑기 (py/transformerlib/sample.py 의 C 판).
 *
 * 새 토큰 하나를 더할 때 앞 위치의 키·값은 변하지 않는다(인과 마스크).
 * 그래서 블록마다 키·값을 [T, d] 로 쌓아 두고, 새 위치의 질의 하나만
 * 계산한다. 토큰 하나가 O(L·(d² + n·d) + V·d) 다.
 *
 * 연산의 차례는 model.c 의 배치 순전파와 같다. 같은 float32 연산을 같은
 * 차례로 하므로 캐시 로짓은 전체 로짓과 사실상 비트까지 같다.
 */
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "ops.h"
#include "sample.h"

#define P(l, name) tfs_tensor(m, m->params, l, name)

void tfs_kv_init(tfs_kv *kv, const tfs_model *m)
{
    const tfs_config *c = &m->c;
    size_t d = (size_t)c->d;
    memset(kv, 0, sizeof *kv);
    kv->m = m;
    kv->k = calloc((size_t)c->L * (size_t)c->T * d, sizeof(float));
    kv->v = calloc((size_t)c->L * (size_t)c->T * d, sizeof(float));
    kv->x = calloc(d, sizeof(float));
    kv->a = calloc(d, sizeof(float));
    kv->xhat = calloc(d, sizeof(float));
    kv->qkv = calloc(3 * d, sizeof(float));
    kv->att = calloc((size_t)c->T, sizeof(float));
    kv->z = calloc((size_t)c->T, sizeof(float));
    kv->o = calloc(d, sizeof(float));
    kv->f = calloc((size_t)c->d_ff, sizeof(float));
    kv->logits = calloc((size_t)c->V, sizeof(float));
}

void tfs_kv_free(tfs_kv *kv)
{
    free(kv->k), free(kv->v), free(kv->x), free(kv->a), free(kv->xhat);
    free(kv->qkv), free(kv->att), free(kv->z), free(kv->o), free(kv->f);
    free(kv->logits);
    memset(kv, 0, sizeof *kv);
}

void tfs_kv_reset(tfs_kv *kv)
{
    kv->n = 0;
}

/* y = x W + b, 한 행. model.c 의 lin_fwd_rows 와 같은 i-k-j. */
static void linear1(float *y, const float *x, const float *W,
                    const float *b, int in, int out)
{
    int k, j;
    memset(y, 0, sizeof(float) * (size_t)out);
    for (k = 0; k < in; k++)
        for (j = 0; j < out; j++)
            y[j] += x[k] * W[k * out + j];
    for (j = 0; j < out; j++)
        y[j] += b[j];
}

static void rope1(float *u, int t, int h, int dk)
{
    int j, i;
    for (j = 0; j < h; j++)
        for (i = 0; i < dk / 2; i++) {
            float *p = u + j * dk + 2 * i;
            double th = t * (1.0 / pow(10000.0, 2.0 * i / dk));
            double cs = cos(th), sn = sin(th), a = p[0], b = p[1];
            p[0] = (float)(a * cs - b * sn);
            p[1] = (float)(a * sn + b * cs);
        }
}

const float *tfs_kv_step(tfs_kv *kv, int token)
{
    const tfs_model *m = kv->m;
    const tfs_config *c = &m->c;
    int d = c->d, h = c->h, dk = d / h, T = c->T, pos = kv->n;
    int l, e, j, t;
    double inv = 1.0 / sqrt((double)dk);
    float sinv, *x = kv->x;

    if (pos >= T)
        return NULL;
    memcpy(x, P(-1, "wte") + token * d, sizeof(float) * (size_t)d);
    if (c->pos == 0) {
        const float *w = P(-1, "wpe") + pos * d;
        for (e = 0; e < d; e++)
            x[e] += w[e];
    } else if (c->pos == 1) {
        for (e = 0; e < d; e += 2) {
            double om = 1.0 / pow(10000.0, 2.0 * (e / 2) / d);
            x[e] = (float)(x[e] + sin(pos * om));
            x[e + 1] = (float)(x[e + 1] + cos(pos * om));
        }
    }
    for (l = 0; l < c->L; l++) {
        float *K = kv->k + ((size_t)l * T + pos) * d;
        float *Vv = kv->v + ((size_t)l * T + pos) * d;
        const float *q = kv->qkv;
        tfs_layernorm_forward(kv->a, kv->xhat, &sinv, x, P(l, "ln1_g"),
                              P(l, "ln1_b"), 1, d);
        linear1(kv->qkv, kv->a, P(l, "Wqkv"), P(l, "bqkv"), d, 3 * d);
        memcpy(K, kv->qkv + d, sizeof(float) * (size_t)d);
        memcpy(Vv, kv->qkv + 2 * d, sizeof(float) * (size_t)d);
        if (c->pos == 2) {
            rope1(kv->qkv, pos, h, dk);
            rope1(K, pos, h, dk);
        }
        for (j = 0; j < h; j++) {
            float *o = kv->o + j * dk;
            for (t = 0; t <= pos; t++) {
                const float *kt = kv->k + ((size_t)l * T + t) * d
                                  + j * dk;
                float acc = 0.0f;
                for (e = 0; e < dk; e++)
                    acc += q[j * dk + e] * kt[e];
                kv->z[t] = (float)(acc * inv);
            }
            tfs_softmax_row(kv->att, kv->z, pos + 1);
            memset(o, 0, sizeof(float) * (size_t)dk);
            for (t = 0; t <= pos; t++) {
                const float *vt = kv->v + ((size_t)l * T + t) * d
                                  + j * dk;
                for (e = 0; e < dk; e++)
                    o[e] += kv->att[t] * vt[e];
            }
        }
        linear1(kv->a, kv->o, P(l, "Wo"), P(l, "bo"), d, d);
        for (e = 0; e < d; e++)
            x[e] = x[e] + kv->a[e];
        tfs_layernorm_forward(kv->a, kv->xhat, &sinv, x, P(l, "ln2_g"),
                              P(l, "ln2_b"), 1, d);
        linear1(kv->f, kv->a, P(l, "W1"), P(l, "b1"), d, c->d_ff);
        tfs_gelu_forward(kv->f, kv->f, c->d_ff);
        linear1(kv->a, kv->f, P(l, "W2"), P(l, "b2"), c->d_ff, d);
        for (e = 0; e < d; e++)
            x[e] = x[e] + kv->a[e];
    }
    kv->n++;
    tfs_layernorm_forward(kv->a, kv->xhat, &sinv, x, P(-1, "lnf_g"),
                          P(-1, "lnf_b"), 1, d);
    {
        const float *W = P(-1, "wte");
        memset(kv->logits, 0, sizeof(float) * (size_t)c->V);
        for (e = 0; e < d; e++)
            for (t = 0; t < c->V; t++)
                kv->logits[t] += kv->a[e] * W[t * d + e];
    }
    return kv->logits;
}

/* ---- 뽑기 (SPEC §7) ---- */
static const double *sort_p;

/* 확률 내림차순, 같으면 작은 id 먼저 */
static int by_prob(const void *x, const void *y)
{
    int i = *(const int *)x, j = *(const int *)y;
    if (sort_p[i] != sort_p[j])
        return sort_p[i] > sort_p[j] ? -1 : 1;
    return i - j;
}

/* 남은 (id, 확률) 을 차례로 ids·probs 에. 개수를 준다.
 * top_k ≤ 0 이면 top-k 없음, top_p ≤ 0 이면 top-p 없음. */
int tfs_filtered(const float *logits, int V, double temp, int top_k,
                 double top_p, int *ids, double *probs)
{
    double *p = malloc(sizeof(double) * (size_t)V), mx, s = 0.0;
    int i, n = V;

    mx = logits[0] / temp;
    for (i = 1; i < V; i++)
        if (logits[i] / temp > mx)
            mx = logits[i] / temp;
    for (i = 0; i < V; i++)
        s += exp(logits[i] / temp - mx);
    for (i = 0; i < V; i++) {
        p[i] = exp(logits[i] / temp - mx) / s;
        ids[i] = i;
    }
    sort_p = p;
    qsort(ids, (size_t)V, sizeof(int), by_prob);
    if (top_k > 0 && top_k < n)
        n = top_k;
    s = 0.0;
    for (i = 0; i < n; i++)
        s += p[ids[i]];
    for (i = 0; i < n; i++)
        probs[i] = p[ids[i]] / s;
    if (top_p > 0.0) {
        double acc = 0.0;
        for (i = 0; i < n; i++) {
            acc += probs[i];
            if (acc >= top_p) {
                n = i + 1;
                break;
            }
        }
        s = 0.0;
        for (i = 0; i < n; i++)
            s += probs[i];
        for (i = 0; i < n; i++)
            probs[i] /= s;
    }
    free(p);
    return n;
}

int tfs_sample_next(const float *logits, int V, double temp, int top_k,
                    double top_p, tfs_rng *r)
{
    int *ids, n, i, pick;
    double *pr, u, acc = 0.0;

    if (temp == 0.0) {                 /* argmax, 동률은 작은 id */
        int best = 0;
        for (i = 1; i < V; i++)
            if (logits[i] > logits[best])
                best = i;
        return best;
    }
    ids = malloc(sizeof(int) * (size_t)V);
    pr = malloc(sizeof(double) * (size_t)V);
    n = tfs_filtered(logits, V, temp, top_k, top_p, ids, pr);
    u = tfs_rng_uniform(r);
    pick = ids[n - 1];                 /* 반올림으로 못 고르면 마지막 */
    for (i = 0; i < n; i++) {
        acc += pr[i];
        if (u < acc) {
            pick = ids[i];
            break;
        }
    }
    free(ids);
    free(pr);
    return pick;
}

/* 프롬프트 뒤에 n_new 토큰. 문맥이 T 에 닿으면 뒤쪽 ⌊T/2⌋ 만 남기고
 * 캐시를 다시 채운다(SPEC §7). out 에 프롬프트까지 전부 담고
 * 길이를 준다. */
int tfs_generate(const tfs_model *m, const int *prompt, int np,
                 int n_new, double temp, int top_k, double top_p,
                 uint64_t seed, int *out)
{
    int T = m->c.T, total = np, ctx0 = 0, fed = 0, i;
    const float *row = NULL;
    tfs_kv kv;
    tfs_rng r;

    tfs_rng_seed(&r, seed);
    tfs_kv_init(&kv, m);
    memcpy(out, prompt, sizeof(int) * (size_t)np);
    for (i = 0; i < n_new; i++) {
        if (total - ctx0 >= T) {       /* 문맥이 찼다 */
            ctx0 = total - T / 2;
            tfs_kv_reset(&kv);
            fed = ctx0;
        }
        if (fed < ctx0)
            fed = ctx0;
        while (fed < total)
            row = tfs_kv_step(&kv, out[fed++]);
        out[total++] = tfs_sample_next(row, m->c.V, temp, top_k, top_p,
                                       &r);
    }
    tfs_kv_free(&kv);
    return total;
}
