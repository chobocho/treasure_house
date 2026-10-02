// 슬라이드 p9-v8-nrt-oblivious — 꺼진 코드의 형식은 '모름', C# 8.0
using System;

#nullable disable
static class Legacy
{
    public static string Get(bool b) => b ? "x" : null;
    public static int Len(string s) => s == null ? -1 : s.Length;
}

#nullable enable
class App
{
    static void Main()
    {
        Console.WriteLine(Legacy.Len(null));     // no warning
        string s = Legacy.Get(false);            // no warning
        string? t = Legacy.Get(true);            // also fine
        Console.WriteLine(t.Length);             // no warning
        Console.WriteLine(s.Length);             // no warning
    }
}
