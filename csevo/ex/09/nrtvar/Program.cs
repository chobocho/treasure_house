// 슬라이드 p9-v8-nrt-var — var 는 물음표가 붙은 형식, C# 8.0
#nullable enable
using System;

class App
{
    static void Main()
    {
        string t = "typed";
        var v = "inferred";                // var means string? here
        t = null;                          // CS8600
        v = null;                          // no warning
        Console.WriteLine(v == null);
        v = "again";
        Console.WriteLine(v.Length);       // not null again: fine
        Console.WriteLine(t ?? "t was null");
    }
}
