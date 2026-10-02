// 슬라이드 p7-v6-interp-const10 — 상수 보간 문자열, C# 10.0
using System;

class App
{
    const string Product = "csevo";
    const string Version = "1";
    const string Agent = $"{Product}/{Version}";   // C# 10

    [Obsolete($"use {nameof(NewApi)} instead")]
    static void OldApi() { }
    static void NewApi() { }

    static void Main()
    {
        Console.WriteLine(Agent);
        switch ("csevo/1")
        {
            case Agent: Console.WriteLine("case matched"); break;
        }
        var a = (ObsoleteAttribute)Attribute.GetCustomAttribute(
            typeof(App).GetMethod("OldApi",
                System.Reflection.BindingFlags.NonPublic |
                System.Reflection.BindingFlags.Static),
            typeof(ObsoleteAttribute));
        Console.WriteLine(a.Message);
    }
}
