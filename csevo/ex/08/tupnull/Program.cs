// 슬라이드 p8-v7-tuple-null — 형식이 없는 원소와 대상 형식, C# 7.0
using System;

class App
{
    static void Main()
    {
        (string name, int n) a = (null, 1);     // target-typed: fine
        Console.WriteLine((a.name ?? "null") + " " + a.n);
        (long, double) b = (1, 2);              // int literals widen
        Console.WriteLine(b.Item1.GetType().Name + " "
            + b.Item2.GetType().Name);
        Func<int, int> twice = x => x * 2;
        (Func<int, int> f, int v) c = (twice, 3);
        Console.WriteLine(c.f(c.v));
#if BAD
        var d = (null, 1);                      // no natural type
        var e = (x => x, 1);
#endif
    }
}
