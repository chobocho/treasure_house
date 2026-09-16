/* tokenizer.c — 바이트 BPE 인코더 (SPEC.md §5).
 *
 * 병합을 **배우는** 일은 파이썬이 한다. C 는 .vocab·.merges 를 읽어
 * 같은 규칙으로 잘라 붙이기만 한다. 결과 .bin 은 파이썬과 바이트까지
 * 같아야 한다(시험이 말뭉치 45개 파일 전부를 견준다).
 *
 * 병합 순위 찾기는 (왼 id, 오른 id) → 순위 해시표로 O(1) 평균이다.
 * 조각 하나의 인코드는 O(len² · 적용된 병합 수)이고 조각은 짧다.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tokenizer.h"

static unsigned hash_pair(int l, int r)
{
    unsigned h = (unsigned)l * 2654435761u ^ (unsigned)r * 40503u;
    return h ^ (h >> 15);
}

static int rank_of(const tfs_tokenizer *t, int l, int r)
{
    unsigned mask = (unsigned)t->table_size - 1, i;
    for (i = hash_pair(l, r) & mask;; i = (i + 1) & mask) {
        int k = t->table[i];
        if (k < 0)
            return -1;
        if (t->left[k] == l && t->right[k] == r)
            return k;
    }
}

static int hexval(int c)
{
    if (c >= '0' && c <= '9')
        return c - '0';
    return (c | 32) - 'a' + 10;
}

int tfs_tok_load(tfs_tokenizer *t, const char *prefix)
{
    char path[512], line[4096];
    FILE *fp;
    int cap = 256, i;

    memset(t, 0, sizeof *t);
    snprintf(path, sizeof path, "%s.vocab", prefix);
    if (!(fp = fopen(path, "r")))
        return -1;
    t->tok = malloc(sizeof(char *) * (size_t)cap);
    t->tok_len = malloc(sizeof(int) * (size_t)cap);
    while (fgets(line, sizeof line, fp)) {
        char *hex = strchr(line, '\t');
        int len;
        if (!hex)
            continue;
        hex++;
        len = (int)strcspn(hex, "\r\n") / 2;
        if (t->n_vocab == cap) {
            cap *= 2;
            t->tok = realloc(t->tok, sizeof(char *) * (size_t)cap);
            t->tok_len = realloc(t->tok_len, sizeof(int) * (size_t)cap);
        }
        t->tok[t->n_vocab] = malloc((size_t)len + 1);
        for (i = 0; i < len; i++)
            t->tok[t->n_vocab][i] = (unsigned char)(
                hexval(hex[2 * i]) * 16 + hexval(hex[2 * i + 1]));
        t->tok_len[t->n_vocab++] = len;
    }
    fclose(fp);

    /* 기본 토큰은 한 바이트짜리 줄들 (SPEC §5.1) */
    for (i = 0; i < 256; i++)
        t->base[i] = -1;
    for (i = 0; i < t->n_vocab; i++)
        if (t->tok_len[i] == 1) {
            t->base[t->tok[i][0]] = i;
            t->n_base++;
        }

    snprintf(path, sizeof path, "%s.merges", prefix);
    if (!(fp = fopen(path, "r")))
        return -1;
    cap = 64;
    t->left = malloc(sizeof(int) * (size_t)cap);
    t->right = malloc(sizeof(int) * (size_t)cap);
    while (fgets(line, sizeof line, fp)) {
        int l, r;
        if (sscanf(line, "%d\t%d", &l, &r) != 2)
            continue;
        if (t->n_merges == cap) {
            cap *= 2;
            t->left = realloc(t->left, sizeof(int) * (size_t)cap);
            t->right = realloc(t->right, sizeof(int) * (size_t)cap);
        }
        t->left[t->n_merges] = l;
        t->right[t->n_merges++] = r;
    }
    fclose(fp);

    t->table_size = 16;
    while (t->table_size < 2 * t->n_merges + 1)
        t->table_size *= 2;
    t->table = malloc(sizeof(int) * (size_t)t->table_size);
    for (i = 0; i < t->table_size; i++)
        t->table[i] = -1;
    for (i = 0; i < t->n_merges; i++) {
        unsigned mask = (unsigned)t->table_size - 1;
        unsigned j = hash_pair(t->left[i], t->right[i]) & mask;
        while (t->table[j] >= 0)
            j = (j + 1) & mask;
        t->table[j] = i;
    }
    return 0;
}

void tfs_tok_free(tfs_tokenizer *t)
{
    int i;
    for (i = 0; i < t->n_vocab; i++)
        free(t->tok[i]);
    free(t->tok);
    free(t->tok_len);
    free(t->left);
    free(t->right);
    free(t->table);
    memset(t, 0, sizeof *t);
}

/* SPEC §5.2 부류표. 'S' 공백 · 'W' 줄바꿈류 · 'D' 숫자 · 'P' · 'L'. */
static char char_class(long cp)
{
    if (cp == ' ')
        return 'S';
    if (cp >= 0x09 && cp <= 0x0D)
        return 'W';
    if (cp >= '0' && cp <= '9')
        return 'D';
    if (cp < 0x80)
        return ((cp | 32) >= 'a' && (cp | 32) <= 'z') ? 'L' : 'P';
    if ((cp >= 0x2000 && cp <= 0x206F) || (cp >= 0x3000 && cp <= 0x303F)
        || (cp >= 0xFF00 && cp <= 0xFF65))
        return 'P';
    return 'L';
}

static int in(char c, const char *set)
{
    return c && strchr(set, c) != NULL;
}

/* 조각 시작 바이트 위치를 starts 에(끝에 n 하나 더). 조각 수를 준다. */
int tfs_pretokenize(const unsigned char *s, int n, int *starts)
{
    int *off = malloc(sizeof(int) * (size_t)(n + 1));
    char *cls = malloc((size_t)n + 1);
    int m = 0, b = 0, i, j, count = 0;

    while (b < n) {                   /* UTF-8 → 글자마다 부류·위치 */
        unsigned c = s[b];
        int len = c < 0x80 ? 1 : c < 0xE0 ? 2 : c < 0xF0 ? 3 : 4;
        long cp = len == 1 ? (long)c
                  : (long)(c & (0x7F >> len)), k;
        for (k = 1; k < len && b + k < n; k++)
            cp = (cp << 6) | (s[b + k] & 0x3F);
        off[m] = b;
        cls[m++] = char_class(cp);
        b += len;
    }
    off[m] = n;
    cls[m] = 0;

    for (i = 0; i < m; i = j) {
        char c = cls[i];
        if (c == 'S' && i + 1 < m && in(cls[i + 1], "LDP")) {
            char k = cls[i + 1];
            for (j = i + 2; j < m && cls[j] == k; j++)
                ;
        } else if (c == 'S' || c == 'W') {
            for (j = i + 1; j < m && in(cls[j], "SW"); j++)
                ;
            /* 공백 연속의 마지막 공백은 다음 낱말에게 양보한다 */
            if (j < m && in(cls[j], "LDP") && cls[j - 1] == 'S'
                && j - i >= 2)
                j--;
        } else {
            for (j = i + 1; j < m && cls[j] == c; j++)
                ;
        }
        starts[count++] = off[i];
    }
    starts[count] = n;
    free(off);
    free(cls);
    return count;
}

/* 한 조각: 순위가 가장 낮은 병합을 찾아 그 짝을 왼쪽부터 합친다. */
static int encode_chunk(const tfs_tokenizer *t, int *ids, int len)
{
    for (;;) {
        int best = -1, i, w;
        for (i = 0; i + 1 < len; i++) {
            int r = rank_of(t, ids[i], ids[i + 1]);
            if (r >= 0 && (best < 0 || r < best))
                best = r;
        }
        if (best < 0)
            return len;
        for (i = 0, w = 0; i < len; w++) {
            if (i + 1 < len && ids[i] == t->left[best]
                && ids[i + 1] == t->right[best]) {
                ids[w] = t->n_base + best;
                i += 2;
            } else {
                ids[w] = ids[i++];
            }
        }
        len = w;
    }
}

int tfs_tok_encode(const tfs_tokenizer *t, const unsigned char *s,
                   int n, uint16_t *out, int cap)
{
    int *starts = malloc(sizeof(int) * (size_t)(n + 2));
    int *ids = malloc(sizeof(int) * (size_t)(n + 1));
    int count = tfs_pretokenize(s, n, starts), c, total = 0;

    for (c = 0; c < count; c++) {
        int a = starts[c], len = starts[c + 1] - a, i;
        for (i = 0; i < len; i++) {
            ids[i] = t->base[s[a + i]];
            if (ids[i] < 0) {           /* 조용히 넘기지 않는다 */
                total = -1;
                goto done;
            }
        }
        len = encode_chunk(t, ids, len);
        for (i = 0; i < len; i++) {
            if (total >= cap) {
                total = -1;
                goto done;
            }
            out[total++] = (uint16_t)ids[i];
        }
    }
done:
    free(starts);
    free(ids);
    return total;
}
