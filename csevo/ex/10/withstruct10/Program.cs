// 슬라이드 p10-v9-with-struct10 — 구조체와 익명 형식의 with, C# 10.0
using System;

struct Pixel
{
    public int X;
    public int Y;
}

class App
{
    static void Main()
    {
        Pixel p = new Pixel { X = 1, Y = 2 };
        Pixel q = p with { Y = 5 };          // struct
        Console.WriteLine(q.X + "," + q.Y);
        var a = new { Name = "ann", Age = 3 };
        var b = a with { Age = 4 };          // anonymous type
        Console.WriteLine(b);
    }
}
