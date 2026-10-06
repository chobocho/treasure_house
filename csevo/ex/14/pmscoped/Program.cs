// 슬라이드 p14-v13-pm-scoped — params 스팬은 저절로 scoped, C# 13
using System;
using System.Diagnostics.CodeAnalysis;

class Program
{
    static ReadOnlySpan<int> First(params ReadOnlySpan<int> xs)
    {
#if ESCAPE
        return xs;                  // would let a stack buffer escape
#else
        return xs.ToArray();        // a heap copy may escape
#endif
    }

    static ReadOnlySpan<int> Keep(
        [UnscopedRef] params ReadOnlySpan<int> xs)
        => xs;                      // allowed: caller sees the risk

    static void Main()
    {
        int[] arr = { 7, 8 };
        Console.WriteLine(First(1, 2).Length + " " + Keep(arr)[1]);
    }
}
