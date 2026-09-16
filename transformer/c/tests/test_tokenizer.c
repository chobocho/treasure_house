/* test_tokenizer.c — C 인코더가 파이썬과 **바이트까지 같은** .bin 을
 * 내는가(허용 오차 0, SPEC §9). out/parity_tokens.txt 의 45개 파일마다
 * 토큰 수와 FNV-1a64 지문을 견준다. 사전 토크나이저 결정표도 파이썬
 * 시험과 같은 사례로 본다. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "check.h"
#include "tokenizer.h"

static uint64_t fnv(const uint16_t *ids, int n)
{
    uint64_t h = 0xcbf29ce484222325ULL;
    int i;
    for (i = 0; i < n; i++) {
        unsigned char b[2] = {(unsigned char)(ids[i] & 0xFF),
                              (unsigned char)(ids[i] >> 8)};
        h = (h ^ b[0]) * 0x100000001b3ULL;
        h = (h ^ b[1]) * 0x100000001b3ULL;
    }
    return h;
}

static void chunks_are(const char *text, int count, const char *want[])
{
    int starts[64], n = tfs_pretokenize((const unsigned char *)text,
                                        (int)strlen(text), starts);
    int i, ok = n == count;
    for (i = 0; ok && i < n; i++) {
        int len = starts[i + 1] - starts[i];
        ok = len == (int)strlen(want[i])
             && memcmp(text + starts[i], want[i], (size_t)len) == 0;
    }
    CHECK(ok, "조각 나누기 %s (조각 %d개)", text, n);
}

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
    if (fread(buf, 1, (size_t)*n, fp) != (size_t)*n)
        *n = -1;
    fclose(fp);
    return buf;
}

int main(void)
{
    char line[512];
    FILE *fp;
    int files = 0;

    {
        const char *a[] = {"안녕하세요", " 세계"};
        const char *b[] = {"a", " ", " b"};
        const char *c[] = {"x", "\n\n", "y"};
        const char *d[] = {"12", ".", "5", "%"};
        const char *e[] = {"hi", " ,", "ok"};
        const char *f[] = {"a", " \n", " b"};
        const char *g[] = {"end", "  "};
        const char *h[] = {"123", "+", "456", "=", "7590", "\n"};
        chunks_are("안녕하세요 세계", 2, a);
        chunks_are("a  b", 3, b);
        chunks_are("x\n\ny", 3, c);
        chunks_are("12.5%", 4, d);
        chunks_are("hi ,ok", 3, e);
        chunks_are("a \n b", 3, f);
        chunks_are("end  ", 2, g);
        chunks_are("123+456=7590\n", 6, h);
    }

    fp = fopen("out/parity_tokens.txt", "r");
    CHECK(fp != NULL, "out/parity_tokens.txt 가 없다");
    while (fp && fgets(line, sizeof line, fp)) {
        char file[256], vocab[64], path[512];
        int nbytes, ntok, n = 0, got;
        unsigned long long hash;
        tfs_tokenizer tk;
        unsigned char *text;
        uint16_t *ids;
        if (line[0] == '=' || line[0] == '#')
            continue;
        if (sscanf(line, "%255[^\t]\t%63[^\t]\t%d\t%d\t%llx", file,
                   vocab, &nbytes, &ntok, &hash) != 5)
            continue;
        snprintf(path, sizeof path, "ckpt/tok/%s", vocab);
        CHECK(tfs_tok_load(&tk, path) == 0, "어휘 %s 를 못 읽는다",
              vocab);
        snprintf(path, sizeof path, "corpus/%s", file);
        text = slurp(path, &n);
        CHECK(text && n == nbytes, "%s 크기", file);
        ids = malloc(sizeof(uint16_t) * (size_t)(n + 1));
        got = text ? tfs_tok_encode(&tk, text, n, ids, n + 1) : -1;
        CHECK(got == ntok, "%s: 토큰 %d개, 파이썬 %d개", file, got,
              ntok);
        CHECK(got == ntok && fnv(ids, got) == hash, "%s: .bin 지문",
              file);
        free(ids);
        free(text);
        tfs_tok_free(&tk);
        files++;
    }
    if (fp)
        fclose(fp);
    CHECK(files == 45, "견준 파일 %d개", files);

    {   /* 어휘에 없는 바이트는 조용히 넘기지 않는다 */
        tfs_tokenizer tk;
        uint16_t ids[8];
        tfs_tok_load(&tk, "ckpt/tok/parity");
        CHECK(tfs_tok_encode(&tk, (const unsigned char *)"01x", 3, ids,
                             8) < 0, "모르는 바이트");
        tfs_tok_free(&tk);
    }
    return check_report("test_tokenizer");
}
