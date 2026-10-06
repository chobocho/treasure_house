// 슬라이드 p13-v12-alias — 튜플 형식에 붙인 별칭, C# 12.0
using System;
using Point = (int X, int Y);

class App
{
    static Point Mid(Point a, Point b) =>
        ((a.X + b.X) / 2, (a.Y + b.Y) / 2);

    static void Main()
    {
        Point p = (0, 0), q = (4, 6);
        var m = Mid(p, q);
        Console.WriteLine($"{m} X={m.X} Y={m.Y}");
    }
}
