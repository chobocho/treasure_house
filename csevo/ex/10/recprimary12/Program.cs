// 슬라이드 p10-v9-primary12 — 클래스의 기본 생성자와 레코드, C# 12.0
using System;

record PointR(int X, int Y);                 // C# 9: properties
class PointC(int X, int Y)                   // C# 12: parameters
{
    public int Sum => X + Y;                 // captured
    public void Move() { X++; }              // and mutable
}

class App
{
    static void Main()
    {
        var r = new PointR(1, 2);
        var c = new PointC(1, 2);
        Console.WriteLine(r.X + " " + r);
        c.Move();
        Console.WriteLine(c.Sum + " " + c);
        Console.WriteLine(typeof(PointR).GetProperty("X") != null);
        Console.WriteLine(typeof(PointC).GetProperty("X") != null);
        Console.WriteLine(new PointC(1, 2).Equals(new PointC(1, 2)));
    }
}
