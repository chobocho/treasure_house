// 슬라이드 p8-v7_2-refext — ref·in 확장 메서드, C# 7.2
using System;

struct Vec
{
    public double X, Y;
    public Vec(double x, double y) { X = x; Y = y; }
}

static class VecExt
{
    // C# 3: the receiver is a copy
    public static void ScaleCopy(this Vec v, double k)
        { v.X *= k; v.Y *= k; }

    // C# 7.2: the caller's own variable
    public static void Scale(ref this Vec v, double k)
        { v.X *= k; v.Y *= k; }

    // C# 7.2: no copy, no write
    public static double Len2(in this Vec v) => v.X * v.X + v.Y * v.Y;
}

class App
{
    static void Main()
    {
        var v = new Vec(3, 4);
        v.ScaleCopy(10);
        Console.WriteLine(v.X + "," + v.Y);
        v.Scale(2);
        Console.WriteLine(v.X + "," + v.Y);
        Console.WriteLine(v.Len2());
        Console.WriteLine(new Vec(1, 1).Len2());   // rvalue: ok for in
#if BAD
        new Vec(1, 1).Scale(2);                    // but not for ref
#endif
    }
}
