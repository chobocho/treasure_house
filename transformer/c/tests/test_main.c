/* test_main.c — tfs 명령줄이 약속대로 말하는가 (PLAN.md §3.2 표 8행).
 * make test-c 가 c/tfs 를 먼저 만든다. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <string.h>

#include "check.h"

/* 명령을 돌려 표준 출력 전체를 buf 에 담는다. 종료 코드를 준다. */
static int run(const char *cmd, char *buf, size_t cap)
{
    FILE *fp = popen(cmd, "r");
    size_t n = 0;
    if (!fp)
        return -1;
    n = fread(buf, 1, cap - 1, fp);
    buf[n] = 0;
    return pclose(fp);
}

int main(void)
{
    static char out[1 << 16];

    CHECK(run("./c/tfs count gpt2-small", out, sizeof out) == 0,
          "count 가 실패한다");
    CHECK(strstr(out, "124439808") != NULL, "count: %s", out);

    CHECK(run("./c/tfs count 2 2 2 1 1 4", out, sizeof out) == 0
              && strstr(out, "66") != NULL,
          "SPEC §4.1 풀어 본 예는 66: %s", out);

    /* 토큰 수는 out/parity_tokens.txt 의 줄과 같아야 한다 */
    CHECK(run("./c/tfs tokenize ckpt/tok/ko512 "
              "'corpus/ko/현진건_운수_좋은_날.txt' .build/t.bin",
              out, sizeof out) == 0, "tokenize 실패");
    {
        char want[64];
        FILE *fp = fopen("out/parity_tokens.txt", "r");
        char line[512];
        want[0] = 0;
        while (fp && fgets(line, sizeof line, fp))
            if (strstr(line, "운수_좋은_날")) {
                char f[256], v[64];
                int b, t;
                sscanf(line, "%255[^\t]\t%63[^\t]\t%d\t%d", f, v, &b,
                       &t);
                snprintf(want, sizeof want, "토큰 %d개", t);
            }
        if (fp)
            fclose(fp);
        CHECK(want[0] && strstr(out, want) != NULL, "tokenize: %s / %s",
              out, want);
    }

    CHECK(run("./c/tfs sample ckpt/parity/tiny_learned.ckpt - "
              "--ids 1,2,3 --n 12 --temp 0", out, sizeof out) == 0,
          "sample 실패");
    CHECK(strstr(out, "1 2 3 9 4 4 3 9 9 3 3 4 3 3 3") != NULL,
          "greedy 가 파이썬 자료와 같다: %s", out);

    CHECK(run("./c/tfs nope 2>&1", out, sizeof out) != 0,
          "모르는 명령은 실패해야 한다");
    return check_report("test_main");
}
