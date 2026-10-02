// 슬라이드 p9-v8-nrt-checks — 분석이 알아듣는 null 검사들, C# 8.0
#nullable enable
using System;

class App
{
    static int A(string? s) => s == null ? 0 : s.Length;
    static int B(string? s) => s is null ? 0 : s.Length;
    static int C(string? s) => s is object ? s.Length : 0;
    static int D(string? s) => s is string t ? t.Length : 0;
    static int E(string? s) => s?.Length ?? 0;
    static int F(string? s) => (s ?? "").Length;
    static int G(string? s)
    {
        if (s == null) throw new ArgumentNullException(nameof(s));
        return s.Length;
    }
    static int H(string? s) => string.IsNullOrEmpty(s) ? 0 : s.Length;

    static void Main()
    {
        Console.WriteLine(A("a") + B("bb") + C("ccc") + D(null)
            + E(null) + F(null) + G("g") + H(null));
    }
}
