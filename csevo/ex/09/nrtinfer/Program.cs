// 슬라이드 p9-v8-nrt-infer — 형식 유추가 nullable 을 옮긴다, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;

class App
{
    static T Id<T>(T x) => x;
    static List<T> One<T>(T x) => new List<T> { x };

    static void Main()
    {
        string? maybe = null;
        string sure = "s";
        var a = Id(sure);                   // T = string
        var b = Id(maybe);                  // T = string?
        List<string> c = One(sure);
        List<string> d = One(maybe);        // CS8619: List<string?>
        var e = new[] { "x", maybe };       // string?[]
        string f = e[0];                    // CS8600
        Console.WriteLine(a + (b ?? "-") + c.Count + d.Count + f);
    }
}
