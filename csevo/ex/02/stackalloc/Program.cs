// 슬라이드 p2-v1-stackalloc — 스택에 잡는 배열 stackalloc, C# 1.0
using System;

class App
{
    static unsafe int Fib(int n)
    {
        int* f = stackalloc int[n];          // C# 1: a pointer only
        f[0] = 0;
        f[1] = 1;
        for (int i = 2; i < n; i++)
            f[i] = f[i - 1] + f[i - 2];
        return f[n - 1];
    }

    static unsafe void Main()
    {
        Console.WriteLine("Fib(10) = " + Fib(10));
        int* p = stackalloc int[3];
        Console.WriteLine("fresh: " + p[0] + " " + p[1] + " " + p[2]);
    }
}
