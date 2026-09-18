#include <stdio.h>

static int add(int a, int b)
{
	return a + b;
}

static int sub(int a, int b)
{
	return a - b;
}

int main(void)
{
	int x = 1;
	int y = 2;
	printf("%d\n", add(x, y));
	return 0;
}
