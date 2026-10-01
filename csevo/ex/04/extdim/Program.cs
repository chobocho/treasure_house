// 슬라이드 p4-v3-ext-dim — 기본 구현 메서드와 확장 메서드, C# 8
using System;

interface IGreeter
{
    string Hello() { return "interface default"; }   // C# 8
}

class Plain : IGreeter { }

static class GreeterExt
{
    public static string Hello(this IGreeter g) { return "extension"; }
}

class App
{
    static void Main()
    {
        Plain p = new Plain();
        IGreeter g = p;
        Console.WriteLine("via IGreeter: " + g.Hello()); // member wins
        Console.WriteLine("via Plain:    " + p.Hello()); // no member
    }
}
