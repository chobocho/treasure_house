// 슬라이드 p7-v6-nullcond-lift — 값 형식 결과는 T? 로, C# 6.0
using System;

struct Point
{
    public int X;
    public Point(int x) { X = x; }
}

class Shape
{
    public string Name = "sq";
    public int Sides = 4;
    public Point Origin = new Point(1);
    public bool Closed = true;
}

class App
{
    static string TypeOf<T>(T value)
    {
        Type t = typeof(T);
        Type u = Nullable.GetUnderlyingType(t);
        return u != null ? u.Name + "?" : t.Name;
    }

    static void Main()
    {
        Shape s = new Shape();
        Console.WriteLine("s?.Name     " + TypeOf(s?.Name));
        Console.WriteLine("s?.Sides    " + TypeOf(s?.Sides));
        Console.WriteLine("s?.Origin   " + TypeOf(s?.Origin));
        Console.WriteLine("s?.Origin.X " + TypeOf(s?.Origin.X));
        Console.WriteLine("s?.Closed   " + TypeOf(s?.Closed));
        Console.WriteLine("s.Sides     " + TypeOf(s.Sides));
    }
}
