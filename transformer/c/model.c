/* model.c — GPT 형 디코더 (py/transformerlib/model.py 의 C 판).
 *
 * 파라미터는 float 배열 **하나**에 SPEC §4 체크포인트 차례대로 붙어
 * 있다. 기울기도 같은 모양의 배열 하나다. 그래서 체크포인트 읽기는
 * fread 한 번이고, AdamW 는 배열 하나를 도는 루프 하나다.
 *
 * 순전파는 역전파가 다시 쓸 값(정규화의 x̂·1/σ, 어텐션 가중치, GELU
 * 앞의 값…)을 tfs_acts 에 남긴다. 메모리는 대략
 *   O(L·B·T·(d·10 + d_ff·2 + h·T)) + O(B·T·V)
 * 이고, h·T² 의 어텐션 가중치가 문맥이 길어질 때 가장 먼저 커진다.
 *
 * 더하는 차례는 파이썬 참조와 같게 두었다(행렬곱 i-k-j, 편향은 곱의
 * 합 뒤에). 그래도 float32 라 값은 SPEC §9 의 오차 안에서만 같다.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "model.h"
#include "ops.h"
#include "pool.h"
#include "rng.h"

/* 블록 안의 텐서 — 이름·모양·초기화. 'w' 0.02 · 'r' 0.02/√(2L) ·
 * '1' 하나 · '0' 영. 모양은 block_size() 가 정한다. */
typedef struct {
    const char *name;
    char init;
} spec_row;

static const spec_row BLOCK[12] = {
    {"ln1_g", '1'}, {"ln1_b", '0'}, {"Wqkv", 'w'}, {"bqkv", '0'},
    {"Wo", 'r'},    {"bo", '0'},    {"ln2_g", '1'}, {"ln2_b", '0'},
    {"W1", 'w'},    {"b1", '0'},    {"W2", 'r'},    {"b2", '0'}};

static size_t block_size(const tfs_config *c, int k)
{
    size_t d = (size_t)c->d, f = (size_t)c->d_ff;
    static const int rows[12] = {1, 1, 1, 3, 1, 1, 1, 1, 1, 2, 2, 1};
    switch (k) {
    case 2:  return d * 3 * d;             /* Wqkv [d, 3d] */
    case 4:  return d * d;                 /* Wo   [d, d]  */
    case 8:  return d * f;                 /* W1   [d, d_ff] */
    case 9:  return f;                     /* b1 */
    case 10: return f * d;                 /* W2   [d_ff, d] */
    default: return rows[k] * d;
    }
}

size_t tfs_param_count(const tfs_config *c)
{
    size_t n = (size_t)c->V * (size_t)c->d, per = 0;
    int k;
    if (c->pos == 0)
        n += (size_t)c->T * (size_t)c->d;
    for (k = 0; k < 12; k++)
        per += block_size(c, k);
    return n + (size_t)c->L * per + 2 * (size_t)c->d;
}

/* 이름표를 만든다: wte, (wpe), h0.ln1_g … lnf_b */
static void layout(tfs_model *m)
{
    const tfs_config *c = &m->c;
    int cap = 4 + 12 * c->L, i = 0, l, k;
    size_t off = 0;
    char buf[32];

    m->names = malloc(sizeof(char *) * (size_t)cap);
    m->offsets = malloc(sizeof(size_t) * (size_t)cap);
    m->sizes = malloc(sizeof(size_t) * (size_t)cap);
#define ADD(nm, sz)                                                 \
    do {                                                            \
        m->names[i] = strcpy(malloc(strlen(nm) + 1), nm);           \
        m->offsets[i] = off;                                        \
        m->sizes[i] = (sz);                                         \
        off += (sz);                                                \
        i++;                                                        \
    } while (0)
    ADD("wte", (size_t)c->V * (size_t)c->d);
    if (c->pos == 0)
        ADD("wpe", (size_t)c->T * (size_t)c->d);
    for (l = 0; l < c->L; l++)
        for (k = 0; k < 12; k++) {
            snprintf(buf, sizeof buf, "h%d.%s", l, BLOCK[k].name);
            ADD(buf, block_size(c, k));
        }
    ADD("lnf_g", (size_t)c->d);
    ADD("lnf_b", (size_t)c->d);
#undef ADD
    m->n_tensors = i;
    m->n_params = off;
}

/* base(파라미터 또는 기울기) 안에서 이름으로 텐서를 찾는다. */
float *tfs_tensor(const tfs_model *m, float *base, int layer,
                  const char *name)
{
    char full[32];
    int i;
    if (layer >= 0)
        snprintf(full, sizeof full, "h%d.%s", layer, name);
    else
        snprintf(full, sizeof full, "%s", name);
    for (i = 0; i < m->n_tensors; i++)
        if (strcmp(m->names[i], full) == 0)
            return base + m->offsets[i];
    return NULL;
}

static void setup(tfs_model *m, const tfs_config *c)
{
    memset(m, 0, sizeof *m);
    m->c = *c;
    layout(m);
    m->params = calloc(m->n_params, sizeof(float));
    m->grads = calloc(m->n_params, sizeof(float));
}

/* SPEC §3.5 — 체크포인트 차례로 normal() 을 뽑는다.
 * 편향·LN 은 뽑지 않는다(그래야 뽑는 차례가 파이썬과 맞는다). */
int tfs_model_init(tfs_model *m, const tfs_config *c, uint64_t seed)
{
    tfs_rng r;
    double res = 0.02 / sqrt(2.0 * c->L);
    int i;

    setup(m, c);
    tfs_rng_seed(&r, seed);
    for (i = 0; i < m->n_tensors; i++) {
        const char *dot = strchr(m->names[i], '.');
        const char *nm = dot ? dot + 1 : m->names[i];
        float *p = m->params + m->offsets[i];
        size_t j, n = m->sizes[i];
        char how = 'w';
        int k;
        if (!dot)
            how = strncmp(nm, "lnf_g", 5) == 0   ? '1'
                  : strncmp(nm, "lnf_b", 5) == 0 ? '0'
                                                 : 'w';
        for (k = 0; dot && k < 12; k++)
            if (strcmp(nm, BLOCK[k].name) == 0)
                how = BLOCK[k].init;
        for (j = 0; j < n; j++) {
            if (how == 'w')
                p[j] = (float)(tfs_rng_normal(&r) * 0.02);
            else if (how == 'r')
                p[j] = (float)(tfs_rng_normal(&r) * res);
            else
                p[j] = how == '1' ? 1.0f : 0.0f;
        }
    }
    return 0;
}

int tfs_model_from_ckpt(tfs_model *m, const char *path)
{
    FILE *fp = fopen(path, "rb");
    char magic[4];
    int h[7];
    tfs_config c;

    memset(m, 0, sizeof *m);
    if (!fp)
        return -1;
    if (fread(magic, 1, 4, fp) != 4 || memcmp(magic, "TFS1", 4) != 0
        || fread(h, sizeof(int), 7, fp) != 7) {
        fclose(fp);
        return -1;
    }
    c.V = h[0], c.T = h[1], c.d = h[2], c.L = h[3], c.h = h[4];
    c.d_ff = h[5], c.pos = (h[6] >> 1) & 3;
    setup(m, &c);
    if (fread(m->params, sizeof(float), m->n_params, fp) != m->n_params
        || fgetc(fp) != EOF) {
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}

int tfs_ckpt_save(const tfs_model *m, const char *path)
{
    FILE *fp = fopen(path, "wb");
    const tfs_config *c = &m->c;
    int h[7] = {c->V, c->T, c->d, c->L, c->h, c->d_ff,
                1 | (c->pos << 1)};
    int ok;

    if (!fp)
        return -1;
    ok = fwrite("TFS1", 1, 4, fp) == 4
         && fwrite(h, sizeof(int), 7, fp) == 7
         && fwrite(m->params, sizeof(float), m->n_params, fp)
                == m->n_params;
    return (fclose(fp) == 0 && ok) ? 0 : -1;
}

void tfs_zero_grad(tfs_model *m)
{
    memset(m->grads, 0, sizeof(float) * m->n_params);
}

#define NEW(n) calloc((size_t)(n), sizeof(float))

void tfs_model_alloc(tfs_model *m, int B, int T)
{
    const tfs_config *c = &m->c;
    int n = B * T, d = c->d, l;

    m->B = B, m->T = T;
    m->a.h = calloc((size_t)c->L, sizeof(tfs_block_acts));
    for (l = 0; l < c->L; l++) {
        tfs_block_acts *a = &m->a.h[l];
        a->x_in = NEW(n * d);
        a->ln1_xhat = NEW(n * d), a->ln1_sinv = NEW(n);
        a->ln1_out = NEW(n * d);
        a->q = NEW(n * d), a->k = NEW(n * d), a->v = NEW(n * d);
        a->att = NEW(B * c->h * T * T);
        a->att_out = NEW(n * d);
        a->x_mid = NEW(n * d);
        a->ln2_xhat = NEW(n * d), a->ln2_sinv = NEW(n);
        a->ln2_out = NEW(n * d);
        a->fc1 = NEW(n * c->d_ff), a->fc1_act = NEW(n * c->d_ff);
    }
    m->a.x_out = NEW(n * d);
    m->a.lnf_xhat = NEW(n * d), m->a.lnf_sinv = NEW(n);
    m->a.lnf_out = NEW(n * d);
    m->a.logits = NEW(n * c->V), m->a.probs = NEW(n * c->V);
    m->a.nll = NEW(n);
    m->a.t3d = NEW(n * 3 * d), m->a.td = NEW(n * d);
    m->a.td2 = NEW(n * d), m->a.tff = NEW(n * c->d_ff);
    m->a.g3d = NEW(n * 3 * d), m->a.gd = NEW(n * d);
    m->a.gd2 = NEW(n * d), m->a.gff = NEW(n * c->d_ff);
    m->a.gV = NEW(n * c->V);
}

void tfs_model_free(tfs_model *m)
{
    int l, i;
    for (l = 0; m->a.h && l < m->c.L; l++) {
        tfs_block_acts *a = &m->a.h[l];
        free(a->x_in), free(a->ln1_xhat), free(a->ln1_sinv);
        free(a->ln1_out), free(a->q), free(a->k), free(a->v);
        free(a->att), free(a->att_out);
        free(a->x_mid), free(a->ln2_xhat), free(a->ln2_sinv);
        free(a->ln2_out), free(a->fc1), free(a->fc1_act);
    }
    free(m->a.h);
    free(m->a.x_out), free(m->a.lnf_xhat), free(m->a.lnf_sinv);
    free(m->a.lnf_out), free(m->a.logits), free(m->a.probs);
    free(m->a.nll), free(m->a.t3d), free(m->a.td), free(m->a.td2);
    free(m->a.tff), free(m->a.g3d), free(m->a.gd), free(m->a.gd2);
    free(m->a.gff), free(m->a.gV);
    for (i = 0; i < m->n_tensors; i++)
        free((char *)m->names[i]);
    free((void *)m->names), free(m->offsets), free(m->sizes);
    free(m->params), free(m->grads);
    memset(m, 0, sizeof *m);
}

/* ---- 병렬 커널 ----
 * 모든 커널이 같은 약속을 지킨다: 출력 칸 하나는 한 조각에서만,
 * 행(또는 가중치 행) 번호가 작은 것부터 더한다. */

typedef struct {
    float *out, *dx, *dW;
    const float *x, *W, *dy;
    int in, outn, rows;
} lin_ctx;

/* Y = X W + b 의 곱 부분. 행 r 마다 i-k-j. */
static void lin_fwd_rows(void *p, int lo, int hi)
{
    lin_ctx *c = p;
    int r, k, j;
    for (r = lo; r < hi; r++) {
        float *o = c->out + r * c->outn;
        const float *xr = c->x + r * c->in;
        memset(o, 0, sizeof(float) * (size_t)c->outn);
        for (k = 0; k < c->in; k++) {
            float xk = xr[k];
            const float *w = c->W + k * c->outn;
            for (j = 0; j < c->outn; j++)
                o[j] += xk * w[j];
        }
    }
}

static void linear_fwd(float *out, const float *x, const float *W,
                       const float *b, int rows, int in, int outn)
{
    lin_ctx c;
    int r, j;
    memset(&c, 0, sizeof c);
    c.out = out, c.x = x, c.W = W, c.in = in, c.outn = outn;
    tfs_parallel_for(rows, lin_fwd_rows, &c);
    for (r = 0; r < rows; r++)             /* 편향은 곱의 합 뒤에 */
        for (j = 0; j < outn; j++)
            out[r * outn + j] += b[j];
}

/* dX[r][k] += Σ_j dY[r][j]·W[k][j] — 행 r 마다 */
static void lin_dx_rows(void *p, int lo, int hi)
{
    lin_ctx *c = p;
    int r, k, j;
    for (r = lo; r < hi; r++)
        for (k = 0; k < c->in; k++) {
            double s = 0.0;
            for (j = 0; j < c->outn; j++)
                s += (double)c->dy[r * c->outn + j]
                     * c->W[k * c->outn + j];
            c->dx[r * c->in + k] += (float)s;
        }
}

/* dW[k][j] += Σ_r X[r][k]·dY[r][j] — 가중치 행 k 마다,
 * r 은 작은 것부터 */
static void lin_dw_rows(void *p, int lo, int hi)
{
    lin_ctx *c = p;
    int r, k, j;
    for (k = lo; k < hi; k++) {
        float *dw = c->dW + k * c->outn;
        for (r = 0; r < c->rows; r++) {
            float xk = c->x[r * c->in + k];
            const float *g = c->dy + r * c->outn;
            for (j = 0; j < c->outn; j++)
                dw[j] += xk * g[j];
        }
    }
}

static void linear_bwd(float *dx, float *dW, float *db, const float *dy,
                       const float *x, const float *W, int rows, int in,
                       int outn)
{
    lin_ctx c;
    int r, j;
    memset(&c, 0, sizeof c);
    c.dx = dx, c.dW = dW, c.dy = dy, c.x = x, c.W = W;
    c.in = in, c.outn = outn, c.rows = rows;
    if (dx)
        tfs_parallel_for(rows, lin_dx_rows, &c);
    tfs_parallel_for(in, lin_dw_rows, &c);
    for (r = 0; r < rows; r++)
        for (j = 0; j < outn; j++)
            db[j] += dy[r * outn + j];
}

/* RoPE — 헤드마다 짝 (2i, 2i+1) 을 위치 t 만큼 돌린다.
 * sign = −1 이면 거꾸로(역전파). θ = t · (1/10000^{2i/d_k}) 를 파이썬
 * posenc._omega 와 **같은 차례**로 계산한다 — t/10000^… 로 나누면
 * 반올림이 달라진다. */
static void rope_rows(float *x, int B, int T, int h, int dk,
                      double sign)
{
    int b, t, j, i;
    for (b = 0; b < B; b++)
        for (t = 0; t < T; t++)
            for (j = 0; j < h; j++)
                for (i = 0; i < dk / 2; i++) {
                    float *u = x + (b * T + t) * h * dk + j * dk
                               + 2 * i;
                    double om = 1.0 / pow(10000.0, 2.0 * i / dk);
                    double th = t * om;
                    double cs = cos(th), sn = sign * sin(th);
                    double a = u[0], bb = u[1];
                    u[0] = (float)(a * cs - bb * sn);
                    u[1] = (float)(a * sn + bb * cs);
                }
}

/* ---- 어텐션: (배치, 헤드) 한 쌍이 한 일감 ---- */
typedef struct {
    float *q, *k, *v, *att, *out, *dout, *dq, *dk, *dv;
    int T, h, dk_, d;
} att_ctx;

static void att_fwd_tasks(void *p, int lo, int hi)
{
    att_ctx *c = p;
    int T = c->T, h = c->h, dk = c->dk_, d = c->d, idx, i, t, e;
    double inv = 1.0 / sqrt((double)dk);
    float *z = malloc(sizeof(float) * (size_t)T);

    for (idx = lo; idx < hi; idx++) {
        int b = idx / h, j = idx % h;
        for (i = 0; i < T; i++) {
            const float *qi = c->q + (b * T + i) * d + j * dk;
            float *arow = c->att + (idx * T + i) * T;
            float *o = c->out + (b * T + i) * d + j * dk;
            for (t = 0; t <= i; t++) {
                const float *kt = c->k + (b * T + t) * d + j * dk;
                float acc = 0.0f;
                for (e = 0; e < dk; e++)
                    acc += qi[e] * kt[e];
                z[t] = (float)(acc * inv);
            }
            tfs_softmax_row(arow, z, i + 1);   /* t > i 는 −∞ 와 같다 */
            for (t = i + 1; t < T; t++)
                arow[t] = 0.0f;
            memset(o, 0, sizeof(float) * (size_t)dk);
            for (t = 0; t <= i; t++) {
                const float *vt = c->v + (b * T + t) * d + j * dk;
                for (e = 0; e < dk; e++)
                    o[e] += arow[t] * vt[e];
            }
        }
    }
    free(z);
}

/* 한 행 i 의 역전파:
 *   dw[t] = ⟨dout_i, v_t⟩          dv_t += w[t]·dout_i
 *   ds    = 소프트맥스 역전파(dw) · 1/√d_k
 *   dq_i += Σ_t ds[t]·k_t          dk_t += ds[t]·q_i
 * dv·dk 는 i 가 작은 것부터 쌓는다(파이썬 행렬곱 역전파의 차례). */
static void att_bwd_tasks(void *p, int lo, int hi)
{
    att_ctx *c = p;
    int T = c->T, h = c->h, dk = c->dk_, d = c->d, idx, i, t, e;
    double inv = 1.0 / sqrt((double)dk);
    float *dw = malloc(sizeof(float) * (size_t)T);
    float *ds = malloc(sizeof(float) * (size_t)T);

    for (idx = lo; idx < hi; idx++) {
        int b = idx / h, j = idx % h;
        for (i = 0; i < T; i++) {
            const float *go = c->dout + (b * T + i) * d + j * dk;
            const float *qi = c->q + (b * T + i) * d + j * dk;
            const float *arow = c->att + (idx * T + i) * T;
            float *dqi = c->dq + (b * T + i) * d + j * dk;
            for (t = 0; t <= i; t++) {
                const float *vt = c->v + (b * T + t) * d + j * dk;
                float *dvt = c->dv + (b * T + t) * d + j * dk;
                double acc = 0.0;
                for (e = 0; e < dk; e++) {
                    acc += (double)go[e] * vt[e];
                    dvt[e] += arow[t] * go[e];
                }
                dw[t] = (float)acc;
                ds[t] = 0.0f;
            }
            tfs_softmax_row_backward(ds, arow, dw, i + 1);
            for (t = 0; t <= i; t++)
                ds[t] = (float)(ds[t] * inv);
            for (e = 0; e < dk; e++) {
                double acc = 0.0;
                for (t = 0; t <= i; t++)
                    acc += (double)ds[t]
                           * c->k[(b * T + t) * d + j * dk + e];
                dqi[e] += (float)acc;
            }
            for (t = 0; t <= i; t++) {
                float *dkt = c->dk + (b * T + t) * d + j * dk;
                for (e = 0; e < dk; e++)
                    dkt[e] += ds[t] * qi[e];
            }
        }
    }
    free(dw);
    free(ds);
}

/* ---- 출력: 로짓 = x · wteᵀ 와 교차엔트로피 ---- */
typedef struct {
    const float *x, *wte, *dl;
    float *logits, *probs, *nll, *dx, *dwte;
    const int *targets;
    int d, V, rows;
} out_ctx;

static void logits_rows(void *p, int lo, int hi)
{
    out_ctx *c = p;
    int r, e, t;
    for (r = lo; r < hi; r++) {
        float *o = c->logits + r * c->V;
        memset(o, 0, sizeof(float) * (size_t)c->V);
        for (e = 0; e < c->d; e++) {
            float xe = c->x[r * c->d + e];
            for (t = 0; t < c->V; t++)
                o[t] += xe * c->wte[t * c->d + e];
        }
        if (c->targets)
            c->nll[r] = (float)tfs_cross_entropy_row(
                c->probs + r * c->V, o, c->V, c->targets[r]);
    }
}

static void logits_dx_rows(void *p, int lo, int hi)
{
    out_ctx *c = p;
    int r, e, t;
    for (r = lo; r < hi; r++)
        for (e = 0; e < c->d; e++) {
            double s = 0.0;
            for (t = 0; t < c->V; t++)
                s += (double)c->dl[r * c->V + t] * c->wte[t * c->d + e];
            c->dx[r * c->d + e] += (float)s;
        }
}

static void logits_dwte_rows(void *p, int lo, int hi)
{
    out_ctx *c = p;
    int r, e, t;
    for (t = lo; t < hi; t++)
        for (r = 0; r < c->rows; r++) {
            float g = c->dl[r * c->V + t];
            for (e = 0; e < c->d; e++)
                c->dwte[t * c->d + e] += c->x[r * c->d + e] * g;
        }
}

#define P(l, name) tfs_tensor(m, m->params, l, name)
#define G(l, name) tfs_tensor(m, m->grads, l, name)

double tfs_forward(tfs_model *m, const int *ids, const int *targets,
                   int B, int T)
{
    const tfs_config *c = &m->c;
    int n = B * T, d = c->d, ff = c->d_ff, dk = d / c->h, l, r, e;
    float *wte = P(-1, "wte");
    tfs_acts *A = &m->a;
    att_ctx ac;
    out_ctx oc;
    double loss = 0.0;

    /* 임베딩 + 위치 */
    for (r = 0; r < n; r++) {
        float *x = A->h[0].x_in + r * d;
        int t = r % T;
        memcpy(x, wte + ids[r] * d, sizeof(float) * (size_t)d);
        if (c->pos == 0) {
            const float *w = P(-1, "wpe") + t * d;
            for (e = 0; e < d; e++)
                x[e] += w[e];
        } else if (c->pos == 1) {
            for (e = 0; e < d; e += 2) {
                double om = 1.0 / pow(10000.0, 2.0 * (e / 2) / d);
                x[e] = (float)(x[e] + sin(t * om));
                x[e + 1] = (float)(x[e + 1] + cos(t * om));
            }
        }
    }

    for (l = 0; l < c->L; l++) {
        tfs_block_acts *a = &A->h[l];
        float *next = l + 1 < c->L ? A->h[l + 1].x_in : A->x_out;
        tfs_layernorm_forward(a->ln1_out, a->ln1_xhat, a->ln1_sinv,
                              a->x_in, P(l, "ln1_g"), P(l, "ln1_b"),
                              n, d);
        linear_fwd(A->t3d, a->ln1_out, P(l, "Wqkv"), P(l, "bqkv"), n, d,
                   3 * d);
        for (r = 0; r < n; r++) {
            memcpy(a->q + r * d, A->t3d + r * 3 * d, sizeof(float) * d);
            memcpy(a->k + r * d, A->t3d + r * 3 * d + d,
                   sizeof(float) * d);
            memcpy(a->v + r * d, A->t3d + r * 3 * d + 2 * d,
                   sizeof(float) * d);
        }
        if (c->pos == 2) {
            rope_rows(a->q, B, T, c->h, dk, 1.0);
            rope_rows(a->k, B, T, c->h, dk, 1.0);
        }
        memset(&ac, 0, sizeof ac);
        ac.q = a->q, ac.k = a->k, ac.v = a->v, ac.att = a->att;
        ac.out = a->att_out, ac.T = T, ac.h = c->h;
        ac.dk_ = dk, ac.d = d;
        tfs_parallel_for(B * c->h, att_fwd_tasks, &ac);

        linear_fwd(A->td, a->att_out, P(l, "Wo"), P(l, "bo"), n, d, d);
        for (e = 0; e < n * d; e++)
            a->x_mid[e] = a->x_in[e] + A->td[e];
        tfs_layernorm_forward(a->ln2_out, a->ln2_xhat, a->ln2_sinv,
                              a->x_mid, P(l, "ln2_g"), P(l, "ln2_b"),
                              n, d);
        linear_fwd(a->fc1, a->ln2_out, P(l, "W1"), P(l, "b1"), n, d,
                   ff);
        tfs_gelu_forward(a->fc1_act, a->fc1, n * ff);
        linear_fwd(A->td, a->fc1_act, P(l, "W2"), P(l, "b2"), n, ff, d);
        for (e = 0; e < n * d; e++)
            next[e] = a->x_mid[e] + A->td[e];
    }

    tfs_layernorm_forward(A->lnf_out, A->lnf_xhat, A->lnf_sinv,
                          A->x_out, P(-1, "lnf_g"), P(-1, "lnf_b"), n,
                          d);
    memset(&oc, 0, sizeof oc);
    oc.x = A->lnf_out, oc.wte = wte, oc.logits = A->logits;
    oc.probs = A->probs, oc.nll = A->nll, oc.targets = targets;
    oc.d = d, oc.V = c->V, oc.rows = n;
    tfs_parallel_for(n, logits_rows, &oc);
    if (!targets)
        return 0.0;
    for (r = 0; r < n; r++)                /* 행 차례로 더한다 */
        loss += A->nll[r];
    return loss / n;
}

void tfs_backward(tfs_model *m, const int *ids, const int *targets,
                  int B, int T)
{
    const tfs_config *c = &m->c;
    int n = B * T, d = c->d, ff = c->d_ff, dk = d / c->h, V = c->V;
    int l, r, e;
    tfs_acts *A = &m->a;
    float scale = (float)(1.0 / n), *wte = P(-1, "wte");
    att_ctx ac;
    out_ctx oc;
#define ZERO(buf, cnt) memset(buf, 0, sizeof(float) * (size_t)(cnt))

    /* 로짓의 기울기 (p − y)/N, 그리고 x·wteᵀ 의 역전파 */
    for (r = 0; r < n; r++) {
        memset(A->gV + r * V, 0, sizeof(float) * (size_t)V);
        tfs_cross_entropy_backward_row(A->gV + r * V, A->probs + r * V,
                                       V, targets[r], scale);
    }
    memset(&oc, 0, sizeof oc);
    oc.x = A->lnf_out, oc.wte = wte, oc.dl = A->gV, oc.dx = A->td;
    oc.dwte = G(-1, "wte"), oc.d = d, oc.V = V, oc.rows = n;
    ZERO(A->td, n * d);
    tfs_parallel_for(n, logits_dx_rows, &oc);
    tfs_parallel_for(V, logits_dwte_rows, &oc);
    ZERO(A->gd, n * d);
    tfs_layernorm_backward(A->gd, G(-1, "lnf_g"), G(-1, "lnf_b"), A->td,
                           A->lnf_xhat, A->lnf_sinv, P(-1, "lnf_g"), n,
                           d);

    /* gd 가 잔차 스트림의 기울기다. 블록을 거꾸로 지나며 더해 간다. */
    for (l = c->L - 1; l >= 0; l--) {
        tfs_block_acts *a = &A->h[l];
        float *dq = A->t3d, *dkk = A->t3d + n * d;
        float *dv = A->t3d + 2 * n * d;

        ZERO(A->gff, n * ff);
        linear_bwd(A->gff, G(l, "W2"), G(l, "b2"), A->gd, a->fc1_act,
                   P(l, "W2"), n, ff, d);
        ZERO(A->tff, n * ff);
        tfs_gelu_backward(A->tff, a->fc1, A->gff, n * ff);
        ZERO(A->td, n * d);
        linear_bwd(A->td, G(l, "W1"), G(l, "b1"), A->tff, a->ln2_out,
                   P(l, "W1"), n, d, ff);
        tfs_layernorm_backward(A->gd, G(l, "ln2_g"), G(l, "ln2_b"),
                               A->td, a->ln2_xhat, a->ln2_sinv,
                               P(l, "ln2_g"), n, d);

        ZERO(A->td, n * d);
        linear_bwd(A->td, G(l, "Wo"), G(l, "bo"), A->gd, a->att_out,
                   P(l, "Wo"), n, d, d);
        ZERO(A->t3d, n * 3 * d);
        memset(&ac, 0, sizeof ac);
        ac.q = a->q, ac.k = a->k, ac.v = a->v, ac.att = a->att;
        ac.dout = A->td, ac.dq = dq, ac.dk = dkk, ac.dv = dv;
        ac.T = T, ac.h = c->h, ac.dk_ = dk, ac.d = d;
        tfs_parallel_for(B * c->h, att_bwd_tasks, &ac);
        if (c->pos == 2) {
            rope_rows(dq, B, T, c->h, dk, -1.0);
            rope_rows(dkk, B, T, c->h, dk, -1.0);
        }
        for (r = 0; r < n; r++) {
            memcpy(A->g3d + r * 3 * d, dq + r * d, sizeof(float) * d);
            memcpy(A->g3d + r * 3 * d + d, dkk + r * d,
                   sizeof(float) * d);
            memcpy(A->g3d + r * 3 * d + 2 * d, dv + r * d,
                   sizeof(float) * d);
        }
        ZERO(A->gd2, n * d);
        linear_bwd(A->gd2, G(l, "Wqkv"), G(l, "bqkv"), A->g3d,
                   a->ln1_out, P(l, "Wqkv"), n, d, 3 * d);
        tfs_layernorm_backward(A->gd, G(l, "ln1_g"), G(l, "ln1_b"),
                               A->gd2, a->ln1_xhat, a->ln1_sinv,
                               P(l, "ln1_g"), n, d);
    }

    /* 임베딩: 뽑아 간 행에 더해 돌려준다 */
    {
        float *dwte = G(-1, "wte"), *dwpe = c->pos == 0 ? G(-1, "wpe")
                                                        : NULL;
        for (r = 0; r < n; r++)
            for (e = 0; e < d; e++)
                dwte[ids[r] * d + e] += A->gd[r * d + e];
        for (r = 0; dwpe && r < n; r++)
            for (e = 0; e < d; e++)
                dwpe[(r % T) * d + e] += A->gd[r * d + e];
    }
#undef ZERO
}
