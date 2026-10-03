// 슬라이드 p11-v10-rs-tuple — 튜플을 이름 있는 형식으로, C# 10.0
using System;

record struct MinMax(int Min, int Max);

class App
{
    static (int Min, int Max) RangeOld(int[] xs)
    {
        int lo = int.MaxValue, hi = int.MinValue;
        foreach (int x in xs)
        {
            lo = Math.Min(lo, x);
            hi = Math.Max(hi, x);
        }
        return (lo, hi);
    }

    static MinMax RangeNew(int[] xs)
    {
        var r = new MinMax(int.MaxValue, int.MinValue);
        foreach (int x in xs)
        {
            r.Min = Math.Min(r.Min, x);     // positional: settable
            r.Max = Math.Max(r.Max, x);
        }
        return r;
    }

    static void Main()
    {
        int[] xs = { 4, 1, 7 };
        var t = RangeOld(xs);
        var m = RangeNew(xs);
        Console.WriteLine(t + " / " + m);
        var (lo, hi) = m;                   // Deconstruct
        Console.WriteLine(lo + ".." + hi);
        Console.WriteLine(m is { Min: 1 } ? "starts at 1" : "?");
    }
}
