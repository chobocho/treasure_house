// 슬라이드 p8-v7-pat-disamb — 꺾쇠의 모호성, C# 7.0
using System;

class G<T> { }

class App
{
    static int A = 1, B = 2, C = 3, D = 4, E = 5;
    static void M(params object[] a) => Console.WriteLine(a.Length);

    static void Main()
    {
        var t = (A < B, C > D);         // two comparisons
        Console.WriteLine(t);
        M(A < B, C > D, E);             // three arguments

        object o = new G<int>();
        if (o is G<int> g)              // a declaration pattern
            Console.WriteLine(g.GetType().Name);
    }
}
