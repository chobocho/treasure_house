// 슬라이드 p12-v11-rq-new — new() 제약과 default, C# 11
using System;

struct Point { public required int X; public required int Y; }

class Box { public required string Label { get; set; } }

class Program
{
    static T Make<T>() where T : new() => new T();

    static void Main()
    {
        Point d = default;               // not enforced
        Console.WriteLine("default : {0},{1}", d.X, d.Y);
        Point[] arr = new Point[2];      // not enforced either
        Console.WriteLine("array   : {0},{1}", arr[1].X, arr[1].Y);
        var p = new Point { X = 1, Y = 2 };
        Console.WriteLine("init    : {0},{1}", p.X, p.Y);
        var b = new Box { Label = "ok" };
        Console.WriteLine("box     : " + b.Label);
#if BAD
        Box made = Make<Box>();          // new() constraint
#endif
#if BAD2
        Console.WriteLine(new Point().X);   // new is enforced
#endif
    }
}
