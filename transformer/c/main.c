/* main.c — tfs: 밑바닥부터 만든 트랜스포머의 명령줄.
 *
 *   tfs count gpt2-small | V T d L h d_ff     파라미터 수 세기
 *   tfs tokenize 어휘 입력.txt 출력.bin         BPE 인코드(SPEC §5)
 *   tfs train  --vocab 어휘 --train 글 …      학습(아래 train_main)
 *   tfs sample 체크포인트 어휘|- --prompt 글    생성(SPEC §7)
 *   tfs accuracy 체크포인트 어휘 시험.txt --sep =   과제 정답률
 *   tfs bench                                  행렬곱 세 차례·스레드
 *   tfs parity [스레드]                        파이썬과 나란히 놓은 표
 *
 * 기록 실행(run_all.py)이 전부 이 명령을 부른다. 출력은 사람이 읽는
 * 한국어 표이고, 시간을 재는 bench 말고는 몇 번을 돌려도 같다.
 */
#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "model.h"
#include "parity.h"
#include "pool.h"
#include "sample.h"
#include "tensor.h"
#include "tokenizer.h"
#include "train.h"

static int die(const char *msg)
{
    fprintf(stderr, "tfs: %s\n", msg);
    return 2;
}

/* 파일 전체를 읽는다. 크기는 *n. */
static unsigned char *slurp(const char *path, int *n)
{
    FILE *fp = fopen(path, "rb");
    unsigned char *buf;
    if (!fp)
        return NULL;
    fseek(fp, 0, SEEK_END);
    *n = (int)ftell(fp);
    fseek(fp, 0, SEEK_SET);
    buf = malloc((size_t)*n + 1);
    if (fread(buf, 1, (size_t)*n, fp) != (size_t)*n) {
        fclose(fp);
        free(buf);
        return NULL;
    }
    buf[*n] = 0;
    fclose(fp);
    return buf;
}

/* 글 파일을 어휘로 인코드해 int 배열로. 개수는 *n. */
static int *encode_file(const tfs_tokenizer *tk, const char *path,
                        int *n)
{
    int len, i;
    unsigned char *text = slurp(path, &len);
    uint16_t *ids;
    int *out;
    if (!text)
        return NULL;
    ids = malloc(sizeof(uint16_t) * (size_t)(len + 1));
    *n = tfs_tok_encode(tk, text, len, ids, len + 1);
    free(text);
    if (*n < 0)
        return NULL;
    out = malloc(sizeof(int) * (size_t)(*n + 1));
    for (i = 0; i < *n; i++)
        out[i] = ids[i];
    free(ids);
    return out;
}

static int count_main(int argc, char **argv)
{
    tfs_config c = {50257, 1024, 768, 12, 12, 3072, 0};
    size_t blk, total;
    if (argc == 7) {
        c.V = atoi(argv[1]), c.T = atoi(argv[2]), c.d = atoi(argv[3]);
        c.L = atoi(argv[4]), c.h = atoi(argv[5]);
        c.d_ff = atoi(argv[6]);
    } else if (argc != 2 || strcmp(argv[1], "gpt2-small") != 0) {
        return die("count gpt2-small | count V T d L h d_ff");
    }
    total = tfs_param_count(&c);
    blk = (total - (size_t)c.V * c.d - (size_t)c.T * c.d - 2 * c.d)
          / (size_t)c.L;
    printf("설정  V=%d T=%d d=%d L=%d h=%d d_ff=%d\n", c.V, c.T, c.d,
           c.L, c.h, c.d_ff);
    printf("토큰 임베딩 wte   V·d        %12lu\n",
           (unsigned long)c.V * c.d);
    printf("위치 임베딩 wpe   T·d        %12lu\n",
           (unsigned long)c.T * c.d);
    printf("블록 하나                    %12lu\n", (unsigned long)blk);
    printf("블록 %2d개                    %12lu\n", c.L,
           (unsigned long)blk * c.L);
    printf("마지막 LN        2d          %12lu\n",
           (unsigned long)2 * c.d);
    printf("합계                         %12lu\n",
           (unsigned long)total);
    return 0;
}

static int tokenize_main(int argc, char **argv)
{
    tfs_tokenizer tk;
    int n, *ids, i;
    FILE *fp;
    if (argc != 4)
        return die("tokenize 어휘 입력.txt 출력.bin");
    if (tfs_tok_load(&tk, argv[1]) != 0)
        return die("어휘를 못 읽는다");
    if (!(ids = encode_file(&tk, argv[2], &n)))
        return die("입력을 인코드하지 못했다(어휘에 없는 바이트?)");
    if (!(fp = fopen(argv[3], "wb")))
        return die("출력을 못 연다");
    for (i = 0; i < n; i++) {
        unsigned char b[2] = {(unsigned char)(ids[i] & 0xFF),
                              (unsigned char)(ids[i] >> 8)};
        fwrite(b, 1, 2, fp);
    }
    fclose(fp);
    printf("토큰 %d개 → %s\n", n, argv[3]);
    tfs_tok_free(&tk);
    return 0;
}

/* 명령줄 인자 찾기 — "--이름 값" */
static const char *opt(int argc, char **argv, const char *name,
                       const char *dflt)
{
    int i;
    for (i = 1; i + 1 < argc; i++)
        if (strcmp(argv[i], name) == 0)
            return argv[i + 1];
    return dflt;
}

static int flag(int argc, char **argv, const char *name)
{
    int i;
    for (i = 1; i < argc; i++)
        if (strcmp(argv[i], name) == 0)
            return 1;
    return 0;
}

/* 앞에서부터 겹치지 않는 창으로 잰 평균 손실(train.py eval_loss). */
static double eval_loss(tfs_model *m, const int *tok, int n, int B,
                        int max_batches)
{
    int T = m->c.T, nw = 0, b = 0, i, t;
    int *x = malloc(sizeof(int) * (size_t)(B * T));
    int *y = malloc(sizeof(int) * (size_t)(B * T));
    double total = 0.0;
    int s;
    for (s = 0; s < n - T; s += T)
        nw++;
    for (i = 0; i + B <= nw && b < max_batches; i += B, b++) {
        int r;
        for (r = 0; r < B; r++)
            for (t = 0; t < T; t++) {
                x[r * T + t] = tok[(i + r) * T + t];
                y[r * T + t] = tok[(i + r) * T + t + 1];
            }
        total += tfs_forward(m, x, y, B, T);
    }
    free(x), free(y);
    return b ? total / b : 0.0;
}

static int train_main(int argc, char **argv)
{
    tfs_tokenizer tk;
    tfs_config c;
    tfs_train_cfg tc;
    tfs_model m;
    tfs_adamw o;
    tfs_rng r;
    const char *pos = opt(argc, argv, "--pos", "learned");
    const char *out = opt(argc, argv, "--out", NULL);
    int ntr, nva = 0, ns, t, log_every, eval_every, eval_batches;
    int *train, *valid = NULL, *starts, *x, *y;

    if (!opt(argc, argv, "--vocab", NULL) || !opt(argc, argv, "--train",
                                                  NULL) || !out)
        return die("train --vocab 어휘 --train 글 --out 체크포인트 …");
    if (tfs_tok_load(&tk, opt(argc, argv, "--vocab", NULL)) != 0)
        return die("어휘를 못 읽는다");
    train = encode_file(&tk, opt(argc, argv, "--train", ""), &ntr);
    if (!train)
        return die("학습 글을 인코드하지 못했다");
    if (opt(argc, argv, "--valid", NULL)
        && !(valid = encode_file(&tk, opt(argc, argv, "--valid", ""),
                                 &nva)))
        return die("검증 글을 인코드하지 못했다");

    c.V = tk.n_vocab;
    c.T = atoi(opt(argc, argv, "--T", "16"));
    c.d = atoi(opt(argc, argv, "--d", "32"));
    c.L = atoi(opt(argc, argv, "--L", "2"));
    c.h = atoi(opt(argc, argv, "--h", "4"));
    c.d_ff = atoi(opt(argc, argv, "--dff", "0"));
    if (c.d_ff == 0)
        c.d_ff = 4 * c.d;
    c.pos = !strcmp(pos, "sin") ? 1 : !strcmp(pos, "rope") ? 2 : 0;
    tc.steps = atoi(opt(argc, argv, "--steps", "100"));
    tc.B = atoi(opt(argc, argv, "--batch", "8"));
    tc.lr_max = atof(opt(argc, argv, "--lr", "1e-3"));
    tc.lr_min = atof(opt(argc, argv, "--lr-min", "0"));
    if (tc.lr_min == 0.0)
        tc.lr_min = tc.lr_max / 10.0;
    tc.warmup = atoi(opt(argc, argv, "--warmup", "10"));
    tc.seed = (uint64_t)atoll(opt(argc, argv, "--seed", "1"));
    tc.newline = -1;
    if (flag(argc, argv, "--aligned"))
        tc.newline = tk.base['\n'];
    log_every = atoi(opt(argc, argv, "--log", "50"));
    eval_every = atoi(opt(argc, argv, "--eval", "0"));
    eval_batches = atoi(opt(argc, argv, "--eval-batches", "8"));

    tfs_pool_init(atoi(opt(argc, argv, "--threads", "1")));
    tfs_model_init(&m, &c, tc.seed);
    tfs_model_alloc(&m, tc.B, c.T);
    tfs_adamw_init(&o, m.n_params);
    starts = malloc(sizeof(int) * (size_t)ntr);
    ns = tfs_batch_starts(train, ntr, c.T, tc.newline, starts);
    x = malloc(sizeof(int) * (size_t)(tc.B * c.T));
    y = malloc(sizeof(int) * (size_t)(tc.B * c.T));
    tfs_rng_seed(&r, tc.seed + 1);
    printf("설정 V=%d T=%d d=%d L=%d h=%d d_ff=%d 위치=%s · "
           "파라미터 %lu개 · 학습 토큰 %d개\n", c.V, c.T, c.d, c.L, c.h,
           c.d_ff, pos, (unsigned long)m.n_params, ntr);
    for (t = 1; t <= tc.steps; t++) {
        double lr = tfs_lr_schedule(t, tc.lr_max, tc.lr_min, tc.warmup,
                                    tc.steps);
        double norm, loss;
        tfs_get_batch(train, starts, ns, tc.B, c.T, &r, x, y);
        loss = tfs_train_step(&m, &o, x, y, tc.B, lr, &norm);
        if (t == 1 || t % log_every == 0 || t == tc.steps)
            printf("스텝 %5d  손실 %.4f  학습률 %.2e  노름 %.3f\n", t,
                   loss, lr, norm);
        if (valid && eval_every
            && (t % eval_every == 0 || t == tc.steps))
            printf("스텝 %5d  검증 손실 %.4f\n", t,
                   eval_loss(&m, valid, nva, tc.B, eval_batches));
        fflush(stdout);
    }
    if (tfs_ckpt_save(&m, out) != 0)
        return die("체크포인트를 못 쓴다");
    tfs_pool_free();
    return 0;
}

/* "1,2,3" → ids. 개수를 준다. */
static int parse_ids(const char *s, int *ids, int cap)
{
    int n = 0;
    while (*s && n < cap) {
        ids[n++] = atoi(s);
        while (*s && *s != ',')
            s++;
        if (*s == ',')
            s++;
    }
    return n;
}

static int sample_main(int argc, char **argv)
{
    tfs_model m;
    tfs_tokenizer tk;
    int have_tok = 0, np = 0, n_new, total, i;
    int *ids;
    const char *prompt = opt(argc, argv, "--prompt", NULL);

    if (argc < 3)
        return die("sample 체크포인트 어휘|- --prompt 글 | --ids 1,2");
    if (tfs_model_from_ckpt(&m, argv[1]) != 0)
        return die("체크포인트를 못 읽는다");
    if (strcmp(argv[2], "-") != 0) {
        if (tfs_tok_load(&tk, argv[2]) != 0)
            return die("어휘를 못 읽는다");
        have_tok = 1;
    }
    n_new = atoi(opt(argc, argv, "--n", "32"));
    ids = malloc(sizeof(int) * (size_t)(4096 + n_new));
    if (prompt && have_tok) {
        uint16_t buf[4096];
        np = tfs_tok_encode(&tk, (const unsigned char *)prompt,
                            (int)strlen(prompt), buf, 4096);
        for (i = 0; i < np; i++)
            ids[i] = buf[i];
    } else {
        np = parse_ids(opt(argc, argv, "--ids", "0"), ids, 4096);
    }
    if (np <= 0)
        return die("프롬프트가 비었다");
    tfs_pool_init(1);
    total = tfs_generate(&m, ids, np, n_new,
                         atof(opt(argc, argv, "--temp", "1")),
                         atoi(opt(argc, argv, "--top-k", "0")),
                         atof(opt(argc, argv, "--top-p", "0")),
                         (uint64_t)atoll(opt(argc, argv, "--seed",
                                             "1")),
                         ids);
    printf("ids:");
    for (i = 0; i < total; i++)
        printf(" %d", ids[i]);
    printf("\n");
    if (have_tok) {
        for (i = 0; i < total; i++)
            fwrite(tk.tok[ids[i]], 1, (size_t)tk.tok_len[ids[i]],
                   stdout);
        printf("\n");
    }
    tfs_pool_free();
    return 0;
}

/* 과제 줄마다 구분자까지를 주고 나머지(줄바꿈 포함)를 greedy 로
 * 만든다. */
static int accuracy_main(int argc, char **argv)
{
    tfs_model m;
    tfs_tokenizer tk;
    const char *sep = opt(argc, argv, "--sep", "=");
    int show = atoi(opt(argc, argv, "--show", "5"));
    int limit = atoi(opt(argc, argv, "--limit", "1000000"));
    int len, good = 0, total = 0, shown = 0;
    unsigned char *text, *line;

    if (argc < 4)
        return die("accuracy 체크포인트 어휘 시험.txt --sep =");
    if (tfs_model_from_ckpt(&m, argv[1]) != 0)
        return die("체크포인트를 못 읽는다");
    if (tfs_tok_load(&tk, argv[2]) != 0)
        return die("어휘를 못 읽는다");
    if (!(text = slurp(argv[3], &len)))
        return die("시험 파일을 못 읽는다");
    tfs_pool_init(1);
    for (line = text; *line && total < limit;) {
        unsigned char *end, *cut;
        uint16_t p[256], a[256];
        int ids[512], np, na, i, ok;
        end = (unsigned char *)strchr((char *)line, '\n');
        cut = (unsigned char *)strchr((char *)line, sep[0]);
        if (!end || !cut || cut > end)
            break;
        np = tfs_tok_encode(&tk, line, (int)(cut - line) + 1, p, 256);
        na = tfs_tok_encode(&tk, cut + 1, (int)(end - cut), a, 256);
        for (i = 0; i < np; i++)
            ids[i] = p[i];
        tfs_generate(&m, ids, np, na, 0.0, 0, 0.0, 0, ids);
        for (ok = 1, i = 0; i < na; i++)
            ok &= ids[np + i] == a[i];
        good += ok;
        total++;
        if (shown < show) {
            printf("  %.*s", (int)(cut - line) + 1, (char *)line);
            for (i = 0; i < na; i++)
                if (ids[np + i] != tk.base['\n'])
                    fwrite(tk.tok[ids[np + i]], 1, 1, stdout);
            printf("   정답 %.*s  %s\n", (int)(end - cut) - 1,
                   (char *)cut + 1, ok ? "맞음" : "틀림");
            shown++;
        }
        line = end + 1;
    }
    printf("정답 %d / %d = %.2f%%\n", good, total,
           total ? 100.0 * good / total : 0.0);
    tfs_pool_free();
    free(text);
    return 0;
}

/* ---- bench: 같은 답을 내는 데 드는 시간만 잰다 ---- */
static double now(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

typedef struct {
    float *out;
    const float *a, *b;
    int n, m, p;
} mm_ctx;

static void mm_rows(void *ctx, int lo, int hi)
{
    mm_ctx *c = ctx;
    tfs_matmul_ikj(c->out + lo * c->p, c->a + lo * c->m, c->b, hi - lo,
                   c->m, c->p);
}

static int bench_main(void)
{
    const int N = 384;
    float *a = malloc(sizeof(float) * N * N);
    float *b = malloc(sizeof(float) * N * N);
    float *o = malloc(sizeof(float) * N * N);
    double flops = 2.0 * N * N * N;           /* 곱 하나 + 덧셈 하나 */
    tfs_rng r;
    int i, th;
    const char *names[] = {"ijk", "ikj", "blocked-32"};

    tfs_rng_seed(&r, 3);
    for (i = 0; i < N * N; i++)
        a[i] = (float)tfs_rng_normal(&r);
    for (i = 0; i < N * N; i++)
        b[i] = (float)tfs_rng_normal(&r);
    printf("== 1. 행렬곱 %d×%d, 한 스레드 ==\n", N, N);
    printf("차례          GFLOP/s\n");
    for (i = 0; i < 3; i++) {
        double t0 = now(), dt;
        int reps = 0;
        do {
            if (i == 0)
                tfs_matmul_ijk(o, a, b, N, N, N);
            else if (i == 1)
                tfs_matmul_ikj(o, a, b, N, N, N);
            else
                tfs_matmul_blocked(o, a, b, N, N, N, 32);
            reps++;
            dt = now() - t0;
        } while (dt < 0.5);
        printf("%-12s  %7.3f\n", names[i], flops * reps / dt / 1e9);
    }
    printf("\n== 2. ikj 를 행으로 나눠 스레드 여럿 ==\n");
    printf("스레드   GFLOP/s   1스레드 대비\n");
    {
        double base = 0;
        for (th = 1; th <= 8; th *= 2) {
            mm_ctx c = {o, a, b, N, N, N};
            double t0, dt, rate;
            int reps = 0;
            tfs_pool_init(th);
            t0 = now();
            do {
                tfs_parallel_for(N, mm_rows, &c);
                reps++;
                dt = now() - t0;
            } while (dt < 0.5);
            tfs_pool_free();
            rate = flops * reps / dt / 1e9;
            if (th == 1)
                base = rate;
            printf("%6d   %7.3f   %6.2f배\n", th, rate, rate / base);
        }
    }
    free(a), free(b), free(o);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 2)
        return die("명령: count · tokenize · train · sample · "
                   "accuracy · bench");
    if (!strcmp(argv[1], "count"))
        return count_main(argc - 1, argv + 1);
    if (!strcmp(argv[1], "tokenize"))
        return tokenize_main(argc - 1, argv + 1);
    if (!strcmp(argv[1], "train"))
        return train_main(argc - 1, argv + 1);
    if (!strcmp(argv[1], "sample"))
        return sample_main(argc - 1, argv + 1);
    if (!strcmp(argv[1], "accuracy"))
        return accuracy_main(argc - 1, argv + 1);
    if (!strcmp(argv[1], "bench"))
        return bench_main();
    if (!strcmp(argv[1], "parity"))
        return tfs_parity_main(argc > 2 ? atoi(argv[2]) : 1);
    return die("모르는 명령");
}
