// 슬라이드 p15-v14-sp-alloc — 스팬 판을 고르면 할당이 없다, C# 14
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

static class E
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int Total(this IEnumerable<int> e)
    {
        int t = 0;
        foreach (int x in e) t += x;     // boxed enumerator
        return t;
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    public static int Total(this ReadOnlySpan<int> s)
    {
        int t = 0;
        foreach (int x in s) t += x;     // no enumerator object
        return t;
    }
}

class Program
{
    static void Main()
    {
        int[] arr = [1, 2, 3];
        int sum = arr.Total();           // warm up
        long before = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) sum += arr.Total();
        long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
        Console.WriteLine("sum " + sum
            + ", bytes per call: " + bytes / 100);
    }
}
