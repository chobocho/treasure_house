// 슬라이드 p8-v7-decon-user — 내 형식의 Deconstruct, C# 7.0
using System;

class Point
{
    public int X { get; }
    public int Y { get; }
    public int Z { get; }
    public Point(int x, int y, int z) { X = x; Y = y; Z = z; }

    // overloads by arity: why Deconstruct uses out parameters
    public void Deconstruct(out int x, out int y)
    {
        x = X; y = Y;
    }
    public void Deconstruct(out int x, out int y, out int z)
    {
        x = X; y = Y; z = Z;
    }
}

class App
{
    static void Main()
    {
        var p = new Point(1, 2, 3);
        var (x, y) = p;             // calls Deconstruct(out, out)
        var (a, b, c) = p;          // the three-out overload
        Console.WriteLine(x + y + " " + (a + b + c));
        (int, int) t = (p.X, p.Y);  // a Point is not a tuple
        Console.WriteLine(t);
#if BAD
        (int, int) u = p;           // deconstructible, not convertible
#endif
    }
}
