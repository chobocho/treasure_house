// 슬라이드 p9-v8-nrt-return — 돌려주는 null, C# 8.0
#nullable enable
using System;

class App
{
    static string Name(int id)
    {
        if (id == 1) return "Ada";
        return null;                       // CS8603
    }

    static string Pick(int id) => id == 1 ? "Ada" : null;   // CS8603

    static string? Find(int id) => id == 1 ? "Ada" : null;  // fine

    static string Cast(object o) => o as string;            // CS8603

    static void Main()
    {
        Console.WriteLine(Name(2) ?? "-");
        Console.WriteLine(Pick(2) ?? "-");
        Console.WriteLine(Find(2) ?? "-");
        Console.WriteLine(Cast(3) ?? "-");
    }
}
