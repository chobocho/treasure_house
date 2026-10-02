// 슬라이드 p7-v6-immut — 레코드 이전의 불변 형식, C# 6.0
using System;

sealed class Point
{
    public int X { get; }
    public int Y { get; }

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }

    public Point WithX(int x) => new Point(x, Y);

    public override bool Equals(object obj)
    {
        Point p = obj as Point;
        return p != null && p.X == X && p.Y == Y;
    }

    public override int GetHashCode() => X * 31 + Y;

    public override string ToString() => "(" + X + ", " + Y + ")";
}

class Program
{
    static void Main()
    {
        Point a = new Point(1, 2);
        Point b = a.WithX(5);
        Console.WriteLine(a + " " + b);
        Console.WriteLine(a.Equals(new Point(1, 2)));
        Console.WriteLine(a == new Point(1, 2));
    }
}
