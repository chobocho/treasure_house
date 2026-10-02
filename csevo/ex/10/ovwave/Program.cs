// 슬라이드 p10-v9-wave5 — 경고 웨이브 5(-warn:5), C# 9.0
using System;

static class Util { }

class App
{
    static void Main()
    {
        object o = "x";
        Console.WriteLine(o is Util);        // CS7023 at -warn:5
        TimeSpan t = TimeSpan.Zero;
        Console.WriteLine(t == null);        // CS8073 at -warn:5
    }
}
