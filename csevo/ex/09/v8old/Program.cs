// 슬라이드 p9-sum-v73 — 같은 프로그램을 C# 7.3 으로, C# 7.3
using System;
using System.Collections.Generic;
using System.IO;

interface IShape { double Area { get; } }
static class Shapes          // shared behaviour: an extension method
{
    public static string Describe(this IShape s) =>
        s.GetType().Name + " " + s.Area.ToString("0.0");
}
class Circle : IShape { public double R; public double Area => R * R; }
class Rect : IShape { public double W, H; public double Area => W * H; }

class App
{
    static List<string> kinds;

    static string Kind(IShape s)
    {
        switch (s)
        {
            case Circle c when c.R == 0: return "point";
            case Circle c: return "round";
            case Rect r when r.W == r.H: return "square";
            default: return "other";
        }
    }

    static IShape Parse(string t)
    {
        string[] p = t.Split(':', 'x');
        if (p[0] == "c") return new Circle { R = D(p[1]) };
        return new Rect { W = D(p[1]), H = D(p[p.Length - 1]) };
        double D(string s) => double.Parse(s);
    }

    static void Main()
    {
        using (var w = new StringWriter())
        {
            foreach (string t in "c:1 r:2x2 r:2x3 c:0".Split(' '))
            {
                IShape s = Parse(t);
                if (kinds == null) kinds = new List<string>();
                kinds.Add(Kind(s));
                w.Write(s.Describe() + " " + Kind(s) + "; ");
            }
            string text = w.ToString();
            Console.WriteLine(text.Substring(0, text.Length - 2));
            Console.WriteLine("last kind: " + kinds[kinds.Count - 1]);
        }
    }
}
