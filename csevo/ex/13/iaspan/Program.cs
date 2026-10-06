// 슬라이드 p13-v12-ia-span — 스팬으로 바뀌는 규칙, C# 12.0
using System;
using System.Runtime.CompilerServices;

[InlineArray(4)] struct Buf { int _e; }

class App
{
    static readonly Buf Ro = default;
    static Buf Get() => default;

    static int Sum(ReadOnlySpan<int> s)
    {
        int t = 0;
        foreach (int v in s) t += v;
        return t;
    }

    static void Main()
    {
        var b = new Buf();
        Span<int> w = b;           // writable variable -> Span
        w.Fill(3);
        ReadOnlySpan<int> r = Ro;  // readonly field -> ReadOnlySpan
        Console.WriteLine(Sum(b) + " " + r.Length + " " + Get()[0]);
#if BAD
        Span<int> s = Ro;          // readonly -> Span
#elif BAD2
        ReadOnlySpan<int> t = Get();   // a value has no location
#endif
    }
}
