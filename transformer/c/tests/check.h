/* check.h — C 시험의 최소 도구.
 *
 * <assert.h> 를 쓰지 않는 까닭: NDEBUG 로 꺼질 수 있고, 첫 실패에서
 * 멈춰 나머지 결과를 못 본다. 실패를 세고 끝에 한 줄로 보고한다.
 */
#ifndef TFS_CHECK_H
#define TFS_CHECK_H

#include <math.h>
#include <stdio.h>

static int check_total, check_failed;

#define CHECK(cond, ...)                                        \
    do {                                                        \
        check_total++;                                          \
        if (!(cond)) {                                          \
            check_failed++;                                     \
            printf("  ✗ %s:%d: ", __FILE__, __LINE__);          \
            printf(__VA_ARGS__);                                \
            printf("\n");                                       \
        }                                                       \
    } while (0)

/* 상대 오차 |a−b| / max(|a|, |b|, 1e-6) — SPEC §9 의 정의 */
static inline double rel_err(double a, double b)
{
    double s = fabs(a) > fabs(b) ? fabs(a) : fabs(b);
    if (s < 1e-6)
        s = 1e-6;
    return fabs(a - b) / s;
}

static inline int check_report(const char *name)
{
    printf("%s: 확인 %d건 · 실패 %d건\n", name, check_total,
           check_failed);
    return check_failed ? 1 : 0;
}

#endif
