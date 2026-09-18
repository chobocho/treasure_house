/* paths.c — 그 경로가 있는가, 실행할 수 있는가 (실험 3).
 *
 *   paths PATH …
 *
 * 리눅스 배포판이라면 당연한 /tmp·/bin/sh·/etc/passwd 가 네이티브
 * Termux 에는 없다. access() 에 물어 errno 이름으로 답한다.
 * 이 기기의 proot 안에서는 Termux 의 바이너리도 우분투의 파일시스템을
 * 보므로 "있음" 이 나온다 — 그 차이가 곧 9부의 이야기다.
 */
#include <errno.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

static const char *errname(int e)
{
	switch (e) {
	case ENOENT: return "ENOENT";
	case EACCES: return "EACCES";
	case ENOTDIR: return "ENOTDIR";
	case EPERM: return "EPERM";
	case ELOOP: return "ELOOP";
	default: return "기타";
	}
}

int main(int argc, char **argv)
{
	struct stat st;
	int i;

	for (i = 1; i < argc; i++) {
		if (stat(argv[i], &st) != 0) {
			printf("%s: 없음 %s\n", argv[i], errname(errno));
			continue;
		}
		/* 디렉터리의 X_OK 는 "들어갈 수 있다" 는 뜻이라 따로 적는다 */
		if (S_ISDIR(st.st_mode))
			printf("%s: 있음 디렉터리\n", argv[i]);
		else if (access(argv[i], X_OK) == 0)
			printf("%s: 있음 실행 가능\n", argv[i]);
		else
			printf("%s: 있음\n", argv[i]);
	}
	return 0;
}
