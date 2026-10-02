// 슬라이드 p9-v8-plan — C# 8.0 에 올 뻔한 대상 형식 new, C# 9.0
using System;

struct Point
{
    public int X, Y;
    public Point(int x, int y) { X = x; Y = y; }
    public override string ToString() => $"({X},{Y})";
}

class App
{
    static void Main()
    {
        Point[] ps = { new (1, 4), new (3, -2), new (9, 5) };
        Console.WriteLine(string.Join(" ", ps));
    }
}
