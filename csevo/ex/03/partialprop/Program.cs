// 슬라이드 p3-v2-partial-later — 구현하는 조각, C# 14
using System;

partial class Point
{
    int x;
    public partial Point(int x) { this.x = x; }
    public partial int X { get { return x; } }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Point(7).X);
    }
}
