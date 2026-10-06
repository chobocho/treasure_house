// 슬라이드 p14-v13-pm-async — async 메서드와 params 스팬, C# 13
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

class Program
{
    static async Task<int> SumAsync(params IReadOnlyList<int> xs)
    {
        await Task.Yield();
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }
#if SPAN
    static async Task<int> SpanAsync(params ReadOnlySpan<int> xs)
    {
        await Task.Yield();
        return xs.Length;
    }
#endif

    static async Task Main() =>
        Console.WriteLine(await SumAsync(1, 2, 3));
}
