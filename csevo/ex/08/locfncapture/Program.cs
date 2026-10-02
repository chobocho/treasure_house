// 슬라이드 p8-v7-locfn-capture — 포착·먼저 부르기·재귀·제네릭, C# 7.0
using System;

class App
{
    static void Main()
    {
        int calls = 0;
        Console.WriteLine(IsEven(10) + " " + IsOdd(7));   // before decl
        Console.WriteLine("calls = " + calls);
        Console.WriteLine(Fib(10).current);
        Console.WriteLine(Pair("a", 1));

        bool IsEven(int n) { calls++; return n == 0 || IsOdd(n - 1); }
        bool IsOdd(int n) { calls++; return n != 0 && IsEven(n - 1); }

        (int current, int previous) Fib(int i)
        {
            if (i == 0) return (1, 0);
            var (p, pp) = Fib(i - 1);
            return (p + pp, p);
        }

        string Pair<T, U>(T t, U u) => t + "/" + u;      // generic
    }
}
