// 슬라이드 p8-v7-pat-later8 — switch 식과 속성 패턴, C# 8.0
using System;

class Rect { public int W { get; set; } public int H { get; set; } }

class App
{
    static string Describe(object o) => o switch
    {
        Rect { W: 0 } => "empty",
        Rect r when r.W == r.H => "square " + r.W,
        Rect r => "rect " + r.W + "x" + r.H,
        null => "null",
        _ => "unknown",
    };

    static void Main()
    {
        Console.WriteLine(Describe(new Rect { W = 2, H = 2 }));
        Console.WriteLine(Describe(new Rect { W = 0, H = 5 }));
        Console.WriteLine(Describe(null));
    }
}
