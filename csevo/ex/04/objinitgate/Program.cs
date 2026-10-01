// 슬라이드 p4-v3-objinit-gate — 객체 초기화자, C# 3.0
using System;

class Point
{
    public int X;
    public int Y;
    public override string ToString()
    {
        return "(" + X + ", " + Y + ")";
    }
}

class App
{
    static void Main()
    {
        Point a = new Point { X = 0, Y = 1 };

        Point b = new Point();            // what it stands for
        b.X = 0;
        b.Y = 1;
        Console.WriteLine(a + " " + b);
    }
}
