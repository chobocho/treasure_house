// 슬라이드 p4-v3-objinit-nested — 중첩 초기화자는 고친다, C# 3.0
using System;

class Point
{
    public int X, Y;
}

class Rectangle
{
    Point p1 = new Point();
    Point p2 = null;                           // never created
    public Point P1 { get { return p1; } }
    public Point P2 { get { return p2; } }
}

class App
{
    static void Main()
    {
        Rectangle r = new Rectangle { P1 = { X = 0, Y = 1 } };
        Console.WriteLine(r.P1.X + "," + r.P1.Y);
        try
        {
            r = new Rectangle { P2 = { X = 2 } };   // P2 is null
        }
        catch (NullReferenceException)
        {
            Console.WriteLine("NullReferenceException");
        }
    }
}
