// 슬라이드 p11-v10-rs-initprop — 위치 속성 하나만 init 으로, C# 10.0
using System;

record struct Order(int Id, int Qty)
{
    public int Id { get; init; } = Id;      // replaces synthesized
}

class App
{
    static void Main()
    {
        var o = new Order(7, 1);
        o.Qty = 3;                          // still mutable
        Console.WriteLine(o);
        var p = o with { Id = 8 };          // init: allowed in with
        Console.WriteLine(p);
#if BAD
        o.Id = 9;
#endif
    }
}
