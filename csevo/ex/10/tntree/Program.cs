// 슬라이드 p10-v9-tn-tree — 식 트리 안의 new(), C# 9.0
using System;
using System.Linq.Expressions;

class Point
{
    public int X, Y;
    public Point(int x, int y) { X = x; Y = y; }
}

class App
{
    static void Main()
    {
        Expression<Func<Point>> e = () => new(1, 2);
        Console.WriteLine(e);
        Console.WriteLine(e.Body.NodeType + " " + e.Body.Type.Name);
        Point p = e.Compile()();
        Console.WriteLine(p.X + p.Y);
    }
}
