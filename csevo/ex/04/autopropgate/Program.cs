// 슬라이드 p4-v3-autoprop-gate — 자동 구현 속성, C# 3.0
using System;

class Point
{
    public int X { get; set; }       // C# 3

    int y;                           // C# 1/2: write it out
    public int Y { get { return y; } set { y = value; } }
}

class App
{
    static void Main()
    {
        Point p = new Point();
        p.X = 3;
        p.Y = 4;
        Console.WriteLine(p.X + p.Y);
    }
}
