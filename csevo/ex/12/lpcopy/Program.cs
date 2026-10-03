// 슬라이드 p12-v11-lp-copy — 배열의 슬라이스는 복사본이다, C# 11
using System;
using System.Linq;

class Program
{
    static int copied;

    static int Sum(int[] a) => a switch
    {
        [] => 0,
        [var first, .. var rest] => first + Track(rest) + Sum(rest),
    };
    static int Track(int[] rest) { copied += rest.Length; return 0; }

    static int SumSpan(ReadOnlySpan<int> s) => s switch
    {
        [] => 0,
        [var first, .. var rest] => first + SumSpan(rest),
    };

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        if (a is [_, .. var r]) r[0] = 99;
        Console.WriteLine("array: a[1] = {0}", a[1]);
        Span<int> s = a;
        if (s is [_, .. var m]) m[0] = 99;
        Console.WriteLine("span : a[1] = {0}", a[1]);

        int[] big = Enumerable.Range(1, 100).ToArray();
        Sum(big); SumSpan(big);            // warm up
        copied = 0;
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        int x = Sum(big);
        long b1 = GC.GetAllocatedBytesForCurrentThread();
        int y = SumSpan(big);
        long b2 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine("Sum     {0}: {1} items copied, {2} bytes",
            x, copied, b1 - b0);
        Console.WriteLine("SumSpan {0}: {1} bytes", y, b2 - b1);
    }
}
