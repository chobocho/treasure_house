// 슬라이드 p9-v8-nrt-flow — 흐름 분석이 null 상태를 따라간다, C# 8.0
#nullable enable
using System;

class App
{
    static int M(string? p)
    {
        if (p == null) return -1;
        return p.Length;                  // not null here: no warning
    }

    static int N(string? p)
    {
        int n = p.Length;                 // CS8602: maybe null
        string s = p;                     // no warning: p was used
        return n + s.Length;
    }

    static void Main()
    {
        Console.WriteLine(M(null) + " " + M("abc"));
        Console.WriteLine(N("abc"));
    }
}
