// 슬라이드 p9-v8-nrt-contexts — 주석 문맥과 경고 문맥, C# 8.0
using System;

class App
{
#nullable enable annotations
    // annotations only: ? means something, no warnings
    static int A(string? p) => p.Length;
    static string B() => null;
#nullable disable annotations
#nullable enable warnings
    // warnings only: types are oblivious, ? is flagged
    static int C(string? p) => p.Length;
    static string D() => null;
#nullable enable
    // both: the full feature
    static int E(string? p) => p.Length;
    static string F() => null;
#nullable disable
    static int G(string p) => p.Length;

    static void Main()
    {
        Console.WriteLine(A("a") + C("c") + E("e") + G("g"));
        Console.WriteLine(B() == null && D() == null && F() == null);
    }
}
