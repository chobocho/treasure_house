/* syscall_loop.c — 시스템 호출 N번 (실험 5, proot 의 값).
 *
 *   syscall_loop N [getpid|getcwd]
 *
 * proot 는 ptrace 로 시스템 호출을 가로채지만 **전부는 아니다** —
 * seccomp 필터에 적은 호출(경로를 다루는 것 등)만 추적자에게 넘기고
 * 나머지는 커널이 곧바로 처리한다(proot src/syscall/seccomp.c).
 * getpid 는 그 목록에 없고 getcwd 는 있다. 둘을 같은 횟수로 돌려
 * 비교하면 "가로챈 호출 하나의 값" 이 드러난다. libc 가 값을 기억해
 * 두는 일을 피하려고 syscall() 로 직접 부른다. 걸린 시간은
 * exp/timeit_exp.py 가 재고, 그 숫자는 스냅샷 캡처로만 싣는다
 * (PLAN.md §0.9).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	char *end;
	long n, i;
	char buf[4096];
	int cwd;

	if (argc < 2 || argc > 3 || (argc == 3 &&
	    strcmp(argv[2], "getpid") && strcmp(argv[2], "getcwd"))) {
		fprintf(stderr, "사용법: syscall_loop N [getpid|getcwd]\n");
		return 2;
	}
	cwd = argc == 3 && !strcmp(argv[2], "getcwd");
	n = strtol(argv[1], &end, 10);
	if (*end != '\0' || n < 0) {
		fprintf(stderr, "N 은 0 이상의 정수\n");
		return 2;
	}
	for (i = 0; i < n; i++) {
		if (cwd)
			syscall(SYS_getcwd, buf, sizeof buf);
		else
			syscall(SYS_getpid);
	}
	printf("%s %ld번\n", cwd ? "getcwd" : "getpid", n);
	return 0;
}
