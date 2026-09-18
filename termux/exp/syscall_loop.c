/* syscall_loop.c — 시스템 호출 N번 (실험 5, proot 의 값).
 *
 *   syscall_loop N
 *
 * proot 는 ptrace 로 모든 시스템 호출을 가로챈다. 호출마다 추적자로
 * 문맥이 두 번 넘어가니, 호출만 잔뜩 하는 프로그램이 가장 크게
 * 느려진다. getpid() 는 libc 가 값을 기억해 두기도 해서 syscall()
 * 로 직접 부른다. 걸린 시간은 exp/timeit_exp.py 가 재고, 그 숫자는
 * 스냅샷 캡처로만 싣는다(PLAN.md §0.9).
 */
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	char *end;
	long n, i;

	if (argc != 2) {
		fprintf(stderr, "사용법: syscall_loop N\n");
		return 2;
	}
	n = strtol(argv[1], &end, 10);
	if (*end != '\0' || n < 0) {
		fprintf(stderr, "N 은 0 이상의 정수\n");
		return 2;
	}
	for (i = 0; i < n; i++)
		syscall(SYS_getpid);
	printf("getpid %ld번\n", n);
	return 0;
}
