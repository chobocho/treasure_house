// 슬라이드 p15-v14-sp-better — 스팬 판을 고르는 오버로드 해석, C# 14
using System;
using System.Collections.Generic;

class Program
{
    static string M(IEnumerable<int> e) => "IEnumerable";
    static string M(ReadOnlySpan<int> s) => "ReadOnlySpan";

    static string N(Span<int> s) => "Span";
    static string N(ReadOnlySpan<int> s) => "ReadOnlySpan";

    static void Main()
    {
        int[] a = [1, 2];
        Console.WriteLine("N(int[]) -> " + N(a));
        Console.WriteLine("N(Span)  -> " + N(a.AsSpan()));
#if AMBIG
        Console.WriteLine("M(int[]) -> " + M(a));
#endif
    }
}
