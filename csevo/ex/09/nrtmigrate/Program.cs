// 슬라이드 p9-v8-nrt-migrate — 옮긴 파일, C# 8.0
#nullable enable
using System;

static class New
{
    public static string? Greet(string? name) =>
        name == null ? null : "hello " + name;
}

class App
{
    static void Main()
    {
        string a = Old.Greet(null);           // oblivious: no warning
        string b = New.Greet(null);           // CS8600
        Console.WriteLine((a ?? "null") + " " + (b ?? "null"));
    }
}
