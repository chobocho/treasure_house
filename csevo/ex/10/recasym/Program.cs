// 슬라이드 p10-v9-rec-asym — 손으로 쓴 Equals 의 비대칭, C# 9.0
using System;

class Point
{
    public int X, Y;
    public override bool Equals(object o) =>
        o is Point p && p.X == X && p.Y == Y;
    public override int GetHashCode() => HashCode.Combine(X, Y);
}

class ColorPoint : Point
{
    public string Color;
    public override bool Equals(object o) =>
        o is ColorPoint c && base.Equals(c) && c.Color == Color;
    public override int GetHashCode() =>
        HashCode.Combine(base.GetHashCode(), Color);
}

class App
{
    static void Main()
    {
        Point p = new Point { X = 1, Y = 2 };
        Point c = new ColorPoint { X = 1, Y = 2, Color = "red" };
        Console.WriteLine("p.Equals(c)  " + p.Equals(c));
        Console.WriteLine("c.Equals(p)  " + c.Equals(p));
    }
}
