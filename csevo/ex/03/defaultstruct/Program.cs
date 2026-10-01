// 슬라이드 p3-v2-default-struct — 구조체의 default(T), C# 2.0
using System;

struct Point
{
    public int X, Y;
    public override string ToString() { return X + "," + Y; }
}

class App
{
    static T Zero<T>() { return default(T); }
    static T Fresh<T>() where T : new() { return new T(); }

    static void Main()
    {
        Point p = Zero<Point>();
        p.X = 3;
        p.Y = 4;
        Console.WriteLine(p + " / " + Fresh<Point>());
        Console.WriteLine(Zero<object>() == null);
        Console.WriteLine(Zero<int?>().HasValue);
    }
}
