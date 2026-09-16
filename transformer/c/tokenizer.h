/* tokenizer.h — SPEC.md §5 의 바이트 BPE 인코더(학습은 파이썬만). */
#ifndef TFS_TOKENIZER_H
#define TFS_TOKENIZER_H

#include <stdint.h>

typedef struct {
    int n_vocab, n_base, n_merges;
    unsigned char **tok;       /* id → 바이트열 */
    int *tok_len;
    int base[256];             /* 바이트 → 기본 토큰 id, 없으면 −1 */
    int *left, *right;         /* 순위 r 의 병합 */
    int *table;                /* (왼, 오) → 순위, 열린 주소 해시 */
    int table_size;
} tfs_tokenizer;

int tfs_tok_load(tfs_tokenizer *t, const char *prefix);
void tfs_tok_free(tfs_tokenizer *t);
int tfs_pretokenize(const unsigned char *s, int n, int *starts);
int tfs_tok_encode(const tfs_tokenizer *t, const unsigned char *s,
                   int n, uint16_t *out, int cap);

#endif
