// 슬라이드 p3-v2-partial-kinds — partial struct·interface, C# 2.0
using System;

partial struct Pt { public int Y; }
partial interface IShape { string Name(); }

class Rect : IShape
{
    Pt corner;
    public Rect(int x, int y) { corner.X = x; corner.Y = y; }
    public int Area() { return corner.X * corner.Y; }
    public string Name() { return "rect"; }
}

class App
{
    static void Main()
    {
        IShape r = new Rect(3, 4);
        Console.WriteLine(r.Name() + " " + r.Area());
        Console.WriteLine(typeof(IShape).GetMethods().Length);
    }
}
