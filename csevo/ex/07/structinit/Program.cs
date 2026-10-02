// 슬라이드 p7-v6-struct-init — 구조체의 속성 초기화자, C# 10.0
using System;

struct Point
{
    public int X { get; } = 5;     // C# 6..9: refused in a struct
    public int Y { get; }

    public Point(int y)            // C# 10: initializers need a ctor
    {
        Y = y;
    }
}

class Program
{
    static void Main()
    {
        Point a = new Point(1);
        Point b = new Point();     // no constructor runs
        Point c = default(Point);
        Console.WriteLine(a.X + " " + a.Y);
        Console.WriteLine(b.X + " " + b.Y);
        Console.WriteLine(c.X + " " + c.Y);
    }
}
