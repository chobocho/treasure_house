// 슬라이드 p9-v8-pat-decon — Deconstruct 는 한 번, C# 8.0
using System;

class Pt
{
    public static int Calls;
    int x, y;
    public Pt(int x, int y) { this.x = x; this.y = y; }
    public void Deconstruct(out int a, out int b)
    {
        Calls++;
        a = x;
        b = y;
    }
}

class App
{
    static string Q(Pt p) => p switch
    {
        (0, 0) => "origin",
        (0, _) => "y axis",
        (_, 0) => "x axis",
        var (a, b) when a > 0 && b > 0 => "first",
        _ => "elsewhere",
    };

    static void Main()
    {
        foreach (var p in new[] { new Pt(0, 0), new Pt(3, 0),
                                  new Pt(2, 2), new Pt(-1, 4) })
        {
            Pt.Calls = 0;
            string q = Q(p);
            Console.WriteLine("{0,-9} Deconstruct x{1}", q, Pt.Calls);
        }
    }
}
