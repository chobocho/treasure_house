/* tfx.h — py/demo/tfx.py 가 쓴 대조 자료(TFX1)를 읽는다.
 *
 * 파일을 통째로 읽어 두고 이름으로 배열을 찾는다. 시험 프로그램이
 * 끝날 때까지 들고 있으므로 해제하지 않는다. 리틀 엔디언 기계를
 * 가정한다(이 저장소의 C 는 전부 그렇다 — SPEC §4).
 */
#ifndef TFS_TFX_H
#define TFS_TFX_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    unsigned char *buf;
    long len;
} tfx_file;

static inline tfx_file tfx_open(const char *path)
{
    tfx_file f = {NULL, 0};
    FILE *fp = fopen(path, "rb");
    if (!fp) {
        printf("  ✗ 대조 자료 없음: %s (parity_fixtures.py)\n", path);
        exit(2);
    }
    fseek(fp, 0, SEEK_END);
    f.len = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    f.buf = malloc((size_t)f.len);
    if (fread(f.buf, 1, (size_t)f.len, fp) != (size_t)f.len)
        exit(2);
    fclose(fp);
    if (f.len < 4 || memcmp(f.buf, "TFX1", 4) != 0)
        exit(2);
    return f;
}

/* 이름이 name 인 배열. 개수는 *n 에. 없으면 NULL. */
static inline double *tfx_get(tfx_file f, const char *name, int *n)
{
    long off = 4;
    while (off < f.len) {
        int nl, k;
        memcpy(&nl, f.buf + off, 4);
        off += 4;
        int hit = (int)strlen(name) == nl
                  && memcmp(f.buf + off, name, (size_t)nl) == 0;
        off += nl;
        memcpy(&k, f.buf + off, 4);
        off += 4;
        if (hit) {
            double *out = malloc(sizeof(double) * (size_t)(k ? k : 1));
            memcpy(out, f.buf + off, 8 * (size_t)k);
            *n = k;
            return out;
        }
        off += 8L * k;
    }
    *n = 0;
    return NULL;
}

static inline float *to_float(const double *x, int n)
{
    float *out = malloc(sizeof(float) * (size_t)(n ? n : 1));
    int i;
    for (i = 0; i < n; i++)
        out[i] = (float)x[i];
    return out;
}

#endif
