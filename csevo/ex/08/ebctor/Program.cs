// 슬라이드 p8-v7-exprbody-ctor — 식 본문 생성자와 튜플 대입, C# 7.0
using System;

class Point
{
    public int X { get; }
    public int Y { get; }

    // one expression assigns both: a tuple on each side
    public Point(int x, int y) => (X, Y) = (x, y);

    // the initializer still comes before =>
    public Point(int both) : this(both, both) =>
        Console.WriteLine("  diagonal " + both);

    public override string ToString() => $"({X}, {Y})";
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Point(1, 2));
        Console.WriteLine(new Point(3));
    }
}
