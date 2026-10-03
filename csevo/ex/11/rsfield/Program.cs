// 슬라이드 p11-v10-rs-field — 위치 매개변수에 대응하는 필드, C# 10.0
using System;

record Point(int X, int Y)
{
    public int X = X;                       // a field, not a property
}

class App
{
    static void Main()
    {
        var p = new Point(1, 2);
        p.X = 10;                           // fields are writable
        Console.WriteLine(p);
        var (x, y) = p;                     // reads the field
        Console.WriteLine(x + " " + y);
        Console.WriteLine(
            typeof(Point).GetField("X") != null);
    }
}
