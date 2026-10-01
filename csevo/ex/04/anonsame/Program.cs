// 슬라이드 p4-v3-anon-same — 같은 모양이면 같은 형식, C# 3.0
using System;

class App
{
    static void Main()
    {
        var p1 = new { Name = "Lawnmower", Price = 495.00 };
        var p2 = new { Name = "Shovel", Price = 26.95 };
        p1 = p2;                                  // same type
        Console.WriteLine(p1);

        var q = new { Price = 26.95, Name = "Shovel" };   // other order
        var r = new { Name = "Shovel", Price = 27 };  // int, not double
        Console.WriteLine(p1.GetType() == q.GetType());
        Console.WriteLine(p1.GetType() == r.GetType());
        Console.WriteLine(p1.Equals(q));
    }
}
