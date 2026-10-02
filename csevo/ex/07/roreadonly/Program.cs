// 슬라이드 p7-v6-roauto-struct — readonly struct 의 재료, C# 7.2
using System;

readonly struct Point
{
    public int X { get; }
    public int Y { get; }

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }
#if BAD
    public int Z { get; set; }
#endif
}

class Program
{
    static void Main()
    {
        Point p = new Point(3, 4);
        Console.WriteLine(p.X + p.Y);
    }
}
