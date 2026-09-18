/* passwd.c — getpwuid() 는 누구에게 묻는가 (실험 2).
 *
 *   passwd [UID …]      인자가 없으면 자기 uid 하나
 *
 * glibc 는 /etc/passwd 를 읽는다. 안드로이드에는 그 파일이 없다.
 * bionic 은 uid 를 보고 이름을 **지어낸다** — 앱 uid 10123 은 u0_a123
 * 이다. Termux 의 clang 으로 지으면 여기에 한 겹이 더 붙는다.
 * termux-packages 의 ndk-patches/pwd.h 가 getpwuid 를 인라인 함수로
 * 덮어써 집을 $HOME, 셸을 $PREFIX/bin/login 으로 바꾼다(5부).
 * 그래서 같은 소스가 두 쪽에서 다른 답을 낸다.
 */
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void show(uid_t uid)
{
	struct passwd *pw = getpwuid(uid);

	if (pw == NULL) {
		printf("uid %u: (없음)\n", (unsigned)uid);
		return;
	}
	printf("uid %u: name=%s dir=%s shell=%s\n", (unsigned)uid,
	       pw->pw_name, pw->pw_dir, pw->pw_shell);
}

int main(int argc, char **argv)
{
	int i;

	if (argc < 2) {
		show(getuid());
		return 0;
	}
	for (i = 1; i < argc; i++)
		show((uid_t)strtoul(argv[i], NULL, 10));
	return 0;
}
