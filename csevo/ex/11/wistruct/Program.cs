// 슬라이드 p11-v10-wi-struct — 아무 구조체에나 with, C# 10.0
using System;

struct Rect
{
    public int W;
    public int H { get; set; }
    public int Area => W * H;
}

class App
{
    static void Main()
    {
        var a = new Rect { W = 2, H = 3 };
        var b = a with { H = 10 };          // field or settable prop
        Console.WriteLine(a.Area + " " + b.Area);
        var c = a with { };                 // just a copy
        c.W = 100;
        Console.WriteLine(a.W + " " + c.W);
        var p = new System.Drawing.Point(1, 2) with { Y = 5 };
        Console.WriteLine(p);
    }
}
