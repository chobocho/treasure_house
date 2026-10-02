// 슬라이드 p8-v7-locfn-lambda — 람다로는 안 되던 것, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        // a recursive lambda needs a variable declared first
        Func<int, int> fact = null;
        fact = n => n <= 1 ? 1 : n * fact(n - 1);
        Console.WriteLine(fact(5) + " " + Fact(5));

        // a local function can be an iterator and generic
        foreach (var s in Repeat("ab", 2)) Console.Write(s + " ");
        Console.WriteLine();

        int Fact(int n) => n <= 1 ? 1 : n * Fact(n - 1);
        IEnumerable<T> Repeat<T>(T v, int k)
        {
            for (int i = 0; i < k; i++) yield return v;
        }
#if BAD
        Func<IEnumerable<int>> it = () => { yield return 1; };
#endif
    }
}
