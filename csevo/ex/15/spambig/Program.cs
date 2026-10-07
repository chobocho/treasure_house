// 슬라이드 p15-v14-sp-ambig — 새로 생긴 모호함, C# 14
using System;

static class Check   // the shape of two xUnit Assert.Equal overloads
{
    public static string Equal<T>(T[] expected, T[] actual) => "T[]";
    public static string Equal<T>(ReadOnlySpan<T> expected,
        Span<T> actual) => "Span";
}

class Program
{
    static void Main()
    {
        long[] x = [2];
        Console.WriteLine(Check.Equal([2], x.AsSpan()));   // workaround
#if OLD
        Console.WriteLine(Check.Equal([2], x));            // C# 13: T[]
#endif
    }
}
