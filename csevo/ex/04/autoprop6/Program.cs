// 슬라이드 p4-v3-autoprop-later — get 만 있는 자동 속성, C# 6
using System;

class Point
{
    public int X { get; }               // C# 6: readonly backing field
    public int Y { get; private set; }    // the C# 3 substitute

    public Point(int x, int y)
    {
        X = x;
        Y = y;
    }
}

class App
{
    static void Main()
    {
        Point p = new Point(3, 4);
        Console.WriteLine(p.X + p.Y);
    }
}
