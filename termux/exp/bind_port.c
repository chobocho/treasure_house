/* bind_port.c — 1024 미만 포트에 bind() 할 수 있는가 (실험 4).
 *
 *   bind_port PORT …            포트마다 한 줄
 *   bind_port --scan FROM TO    같은 답이 이어지는 구간으로 묶어서
 *
 * 리눅스는 1024 미만 포트를 CAP_NET_BIND_SERVICE 가 없으면 막는다.
 * 안드로이드 앱에는 그 능력이 없고, proot 의 가짜 root(uid 0)도
 * 커널이 보기에는 여전히 앱이다. 이 기기에서 훑어 보면 몇몇 포트만
 * 열려 있다 — 그 목록은 캡처(out/)가 말하고, 까닭은 8부가 다룬다.
 * 127.0.0.1 에만 bind 하고 곧바로 닫는다. 바깥에 열리는 일은 없다.
 */
#include <errno.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

/* 0 이면 성공, 아니면 errno. O(1). */
static int try_bind(int port)
{
	struct sockaddr_in a;
	int s = socket(AF_INET, SOCK_STREAM, 0);
	int r;

	if (s < 0)
		return errno;
	memset(&a, 0, sizeof a);
	a.sin_family = AF_INET;
	a.sin_port = htons((unsigned short)port);
	a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	r = bind(s, (struct sockaddr *)&a, sizeof a) == 0 ? 0 : errno;
	close(s);
	return r;
}

static const char *name(int e)
{
	switch (e) {
	case 0: return "ok";
	case EACCES: return "EACCES";
	case EADDRINUSE: return "EADDRINUSE";
	case EPERM: return "EPERM";
	default: return "기타";
	}
}

/* 같은 답이 이어지는 구간을 한 줄로. O(TO-FROM) 번의 bind. */
static void scan(int from, int to)
{
	int start = from, prev = try_bind(from), p, r;

	for (p = from + 1; p <= to + 1; p++) {
		r = p <= to ? try_bind(p) : -1;
		if (r != prev) {
			if (start == p - 1)
				printf("%d: %s\n", start, name(prev));
			else
				printf("%d-%d: %s\n", start, p - 1, name(prev));
			start = p;
			prev = r;
		}
	}
}

int main(int argc, char **argv)
{
	int i;

	if (argc == 4 && strcmp(argv[1], "--scan") == 0) {
		scan(atoi(argv[2]), atoi(argv[3]));
		return 0;
	}
	for (i = 1; i < argc; i++)
		printf("%s: %s\n", argv[i], name(try_bind(atoi(argv[i]))));
	return 0;
}
