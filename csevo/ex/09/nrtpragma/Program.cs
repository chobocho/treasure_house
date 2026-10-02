// 슬라이드 p9-v8-nrt-pragma — #pragma warning 과 nullable, C# 8.0
#nullable enable
using System;

class App
{
    static void A(string? p) { Console.Write(p.Length); }
#pragma warning disable nullable
    static void B(string? p) { Console.Write(p.Length); }
#pragma warning restore nullable
    static void C(string? p) { Console.Write(p.Length); }
#pragma warning disable CS8602
    static void D(string? p) { Console.Write(p.Length); }
#pragma warning restore CS8602

    static void Main() { A("a"); B("b"); C("c"); D("d"); }
}
