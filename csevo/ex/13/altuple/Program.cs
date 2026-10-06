// 슬라이드 p13-v12-al-tuple — 별칭은 새 형식이 아니다, C# 12.0
using System;
using Point = (int X, int Y);
using Size = (int W, int H);

class App
{
    static string Show(Point p) => $"Point {p.X},{p.Y}";
#if OVER
    static string Show(Size s) => $"Size {s.W}x{s.H}";
#endif

    static void Main()
    {
        Size s = (3, 4);
        Console.WriteLine(Show(s));                // Size → Point
        Console.WriteLine(typeof(Point) == typeof(Size));
        Console.WriteLine(typeof(Point));
        var named = (A: 1, B: 2);
        Point p = named;                           // names change
        Console.WriteLine($"{p.X} {p.Item2}");
    }
}
