// 슬라이드 p8-v7-gates-demo — 이 조각의 게이트 다섯, C# 7.0
using System;

class App
{
    static (int min, int max) Range(int[] xs)      // tuples
    {
        int lo = int.MaxValue, hi = int.MinValue;
        foreach (int x in xs)
        {
            lo = Math.Min(lo, x);
            hi = Math.Max(hi, x);
        }
        return (lo, hi);
    }

    static void Main()
    {
        object o = "12";
        if (o is string s                          // pattern matching
            && int.TryParse(s, out int n))         // out variable
        {
            Console.WriteLine(Twice(n));
        }
        var (_, max) = Range(new[] { 3, 9, 4 });   // discards
        Console.WriteLine(max);

        int Twice(int v) => v * 2;                 // local functions
    }
}
