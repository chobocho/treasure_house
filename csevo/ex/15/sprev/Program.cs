// 슬라이드 p15-v14-sp-reverse — 같은 a.Rev() 가 제자리 뒤집기로, C# 14
using System;
using System.Collections.Generic;

static class OldLinq   // the shape of Enumerable.Reverse before .NET 10
{
    public static IEnumerable<T> Rev<T>(this IEnumerable<T> e)
    {
        var list = new List<T>(e);
        list.Reverse();
        return list;
    }
}

static class Mem       // the shape of MemoryExtensions.Reverse
{
    public static void Rev<T>(this Span<T> s) => s.Reverse();
}

class Program
{
    static void Main()
    {
        int[] a = [1, 2, 3];
        a.Rev();                                    // result dropped
        Console.WriteLine(string.Join(",", a));
#if VAR
        var copy = a.Rev();
#endif
    }
}
