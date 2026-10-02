// 슬라이드 p8-v7-pat-switch — 어떤 형식이든 switch, C# 7.0
using System;

class Circle { public double R; }
class Rect { public double W, H; }

class App
{
    static string Describe(object shape)
    {
        switch (shape)                      // object: not integral
        {
            case Circle c:
                return "circle r=" + c.R;
            case Rect r when r.W == r.H:    // a guard
                return "square " + r.W;
            case Rect r:
                return "rect " + r.W + "x" + r.H;
            case null:
                return "null";
            default:
                return "unknown " + shape.GetType().Name;
        }
    }

    static void Main()
    {
        object[] shapes = { new Circle { R = 1 },
            new Rect { W = 2, H = 2 }, new Rect { W = 2, H = 3 },
            null, "x" };
        foreach (var s in shapes) Console.WriteLine(Describe(s));
    }
}
