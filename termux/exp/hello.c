/* hello.c — 같은 소스, 두 libc (실험 1).
 *
 * 한 글자도 다르지 않은 이 파일을 proot 의 gcc(glibc)와 Termux 의
 * clang(bionic)으로 각각 짓는다. 첫 줄은 둘이 같고, 둘째 줄부터
 * 다르다. 다른 까닭은 소스가 아니라 **컴파일러가 가진 헤더와 링커가
 * 붙이는 libc** 다. 그 차이가 ELF 머리의 interp 에 그대로 남는다
 * (py/elf.py 로 읽는다 — 5부).
 */
#include <stdio.h>

int main(void)
{
	puts("hello, termux");
#if defined(__BIONIC__)
	/* bionic 은 안드로이드의 C 라이브러리다. NDK 헤더는 목표로 삼은
	 * API 수준을 __ANDROID_API__ 로 알려 준다 — 그보다 새 함수는
	 * 헤더에서 아예 안 보인다. */
	puts("libc: bionic");
	printf("android api: %d\n", __ANDROID_API__);
#elif defined(__GLIBC__)
	puts("libc: glibc");
	printf("glibc: %d.%d\n", __GLIBC__, __GLIBC_MINOR__);
#else
	puts("libc: (모름)");
#endif
	printf("sizeof(long)=%zu sizeof(void*)=%zu\n", sizeof(long),
	       sizeof(void *));
	return 0;
}
