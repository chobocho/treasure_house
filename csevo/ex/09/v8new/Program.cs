// 슬라이드 p9-sum-v8 — 같은 프로그램을 C# 8.0 으로, C# 8.0
using System;
using System.Collections.Generic;
using System.IO;

interface IShape
{
    double Area { get; }
    string Describe() =>                    // default implementation
        GetType().Name + " " + Area.ToString("0.0");
}
class Circle : IShape { public double R; public double Area => R * R; }
class Rect : IShape { public double W, H; public double Area => W * H; }

class App
{
    static List<string> kinds;

    static string Kind(IShape s) => s switch
    {
        Circle { R: 0 } => "point",
        Circle _ => "round",
        Rect { W: var w, H: var h } when w == h => "square",
        _ => "other",
    };

    static IShape Parse(string t)
    {
        string[] p = t.Split(':', 'x');
        if (p[0] == "c") return new Circle { R = D(p[1]) };
        return new Rect { W = D(p[1]), H = D(p[^1]) };
        static double D(string s) => double.Parse(s);
    }

    static void Main()
    {
        using var w = new StringWriter();
        foreach (string t in "c:1 r:2x2 r:2x3 c:0".Split(' '))
        {
            IShape s = Parse(t);
            kinds ??= new List<string>();
            kinds.Add(Kind(s));
            w.Write(s.Describe() + " " + Kind(s) + "; ");
        }
        string text = w.ToString();
        Console.WriteLine(text[..^2]);
        Console.WriteLine("last kind: " + kinds[^1]);
    }
}
