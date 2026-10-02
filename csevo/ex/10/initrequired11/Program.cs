// 슬라이드 p10-v9-required11 — required 멤버, C# 11.0
using System;

class Order
{
    public required string Customer { get; init; }
    public int Quantity { get; init; }
}

class App
{
    static void Main()
    {
        var o = new Order { Customer = "ann" };
        Console.WriteLine(o.Customer + " " + o.Quantity);
#if BAD
        var bad = new Order { Quantity = 2 };   // Customer missing
#endif
    }
}
