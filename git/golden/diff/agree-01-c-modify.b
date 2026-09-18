#include <stdio.h>

static int add(int a, int b)
{
	return a + b;
}

int main(void)
{
	int x = 1;
	int y = 20;
	printf("%d\n", add(x, y));
	return 0;
}
