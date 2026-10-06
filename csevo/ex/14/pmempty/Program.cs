// 슬라이드 p14-v13-pm-empty — 빈 [] 와 스팬의 우선, C# 13
using System;

class Program
{
    // the breaking-change document's C.M
    static string M(ReadOnlySpan<int> ros) => "ReadOnlySpan<int>";
    static string M(Span<object> s) => "Span<object>";

    static void Main()
    {
        Console.WriteLine("M([1])     " + M([1]));
        Console.WriteLine("M([\"\"])    " + M([""]));
#if EMPTY
        Console.WriteLine("M([])      " + M([]));
#endif
    }
}
