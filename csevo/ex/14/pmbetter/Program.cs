// 슬라이드 p14-v13-pm-better — 원소 형식이 정확한 쪽을 고른다, C# 13
using System;

class Program
{
    // the breaking-change document's M1
    static string M1(ReadOnlySpan<byte> ros) => "ReadOnlySpan<byte>";
    static string M1(Span<int> s) => "Span<int>";

    static string M2(ReadOnlySpan<string> r) => "ReadOnlySpan<string>";
    static string M2(ReadOnlySpan<object> r) => "ReadOnlySpan<object>";

    static void Main()
    {
        Console.WriteLine("M1([1])          " + M1([1]));
        Console.WriteLine("M1([(byte)1])    " + M1([(byte)1]));
#if ELEM
        Console.WriteLine("M2([\"\"])         " + M2([""]));
#endif
        Console.WriteLine("M2([\"\", obj])    "
                          + M2(["", new object()]));
    }
}
