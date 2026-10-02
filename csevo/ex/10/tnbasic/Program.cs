// 슬라이드 p10-v9-targetnew — 대상 형식 new, C# 9.0
using System;
using System.Collections.Generic;

class Point
{
    public int X { get; set; }
    public int Y { get; set; }
    public Point() { }
    public Point(int x, int y) { X = x; Y = y; }
    public override string ToString() => $"({X}, {Y})";
}

class App
{
    // field: the long type is written once
    static readonly Dictionary<string, List<int>> map = new()
    {
        { "a", new() { 1, 2, 3 } }
    };

    static Point Origin() => new();              // return

    static void Show(Point p) => Console.WriteLine(p);

    static void Main()
    {
        Point p = new(3, 5);                      // local
        Point[] ps = { new(1, 2), new(5, -3) };   // array init
        Show(new() { X = 7 });                    // argument
        Console.WriteLine(p + " " + ps[1] + " " + Origin());
        Console.WriteLine(map["a"].Count);
    }
}
