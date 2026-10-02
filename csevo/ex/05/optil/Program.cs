// 슬라이드 p5-v4-opt-callsite — 기본값은 부르는 쪽에 박힌다, C# 4.0
using System;
using System.Reflection;

class Program
{
    static void Greet(string name, int times = 10) { }

    static void OmitDefault() { Greet("Ada"); }

    static void NamedSwap() { Greet(times: 2, name: "Bo"); }

    static int Two() { return 2; }
    static string Bo() { return "Bo"; }
    static void NamedCalls() { Greet(times: Two(), name: Bo()); }

    static void Main()
    {
        BindingFlags f = BindingFlags.NonPublic | BindingFlags.Static;
        Console.WriteLine("OmitDefault:");
        IlDump.Print(typeof(Program).GetMethod("OmitDefault", f));
        Console.WriteLine("NamedSwap:");
        IlDump.Print(typeof(Program).GetMethod("NamedSwap", f));
        Console.WriteLine("NamedCalls:");
        IlDump.Print(typeof(Program).GetMethod("NamedCalls", f));
    }
}
