// 슬라이드 p14-v13-pm-tie — 확장 꼴과 컬렉션 식의 다른 답, C# 13
using System;

class Program
{
    // the proposal's Test2: generic Span<T> vs non-generic int[]
    static string M2<T>(params Span<T> y) => "Span<T>";
    static string M2(params int[] y) => "int[]";

    // the proposal's M2 of the empty-list example
    static string E(params ReadOnlySpan<int> a) => "ReadOnlySpan<int>";
    static string E(params Span<int?> a) => "Span<int?>";

    static void Main()
    {
        Console.WriteLine("M2([1]) " + M2([1]));
        Console.WriteLine("M2(1)   " + M2(1));
        Console.WriteLine("E(1)    " + E(1));
#if NONE
        Console.WriteLine("E()     " + E());
#endif
    }
}
