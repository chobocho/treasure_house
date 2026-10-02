// 슬라이드 p9-v8-readonlymem — readonly 멤버, C# 8.0
using System;

struct Point
{
    public double X { get; set; }
    public double Y { get; set; }

    public readonly double Distance => Math.Sqrt(X * X + Y * Y);

    public readonly override string ToString() =>
        "(" + X + ", " + Y + ") is " + Distance + " from origin";

    public void Translate(double dx, double dy)  // writes: not readonly
    {
        X += dx;
        Y += dy;
    }
}

class App
{
    static void Main()
    {
        var p = new Point { X = 3, Y = 4 };
        Console.WriteLine(p);
        p.Translate(3, 4);
        Console.WriteLine(p);
    }
}
