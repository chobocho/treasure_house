// 슬라이드 p14-v13-ar-natural — 람다의 자연 형식은 Func, C# 13.0
using System;

class App
{
    static void Main()
    {
        var len = (Span<int> s) => s.Length;
        var first = (ReadOnlySpan<char> s) => s[0];
        Span<int> buf = stackalloc int[3];
        Console.WriteLine(len.GetType().Name);
        Console.WriteLine(first.GetType().Name);
        Console.WriteLine(len(buf) + " " + first("xyz"));
    }
}
