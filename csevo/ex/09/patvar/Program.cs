// 슬라이드 p9-v8-varpat — var 패턴과 무시 패턴, C# 8.0
using System;

class App
{
    static (int, int) MinMax(int[] a)
    {
        int lo = a[0], hi = a[0];
        foreach (int x in a)
            (lo, hi) = (Math.Min(lo, x), Math.Max(hi, x));
        return (lo, hi);
    }

    static void Main()
    {
        int[] data = { 4, 9, 1, 7 };
        // var (x, y) is the same as (var x, var y): always matches
        if (MinMax(data) is var (lo, hi) && hi - lo > 5)
            Console.WriteLine("spread {0}..{1}", lo, hi);
        // var binds null too; a type pattern does not
        string s = null;
        Console.WriteLine("{0} {1}", s is var v, s is string);
        // _ inside a pattern is a discard
        Console.WriteLine((1, "a") is (1, _));
#if BAD
        Console.WriteLine(s is _);    // _ is not a pattern here
#endif
    }
}
