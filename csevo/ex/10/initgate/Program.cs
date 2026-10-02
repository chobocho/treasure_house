// 슬라이드 p10-v9-init — init 접근자, C# 9.0
using System;

struct Point
{
    public int X { get; init; }
    public int Y { get; init; }
}

class App
{
    static void Main()
    {
        var p = new Point() { X = 42, Y = 13 };
        Console.WriteLine(p.X + "," + p.Y);
    }
}
