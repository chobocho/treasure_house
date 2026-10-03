// 슬라이드 p11-v10-proppat — 확장 속성 패턴, C# 10.0
using System;

struct Size { public int W, H; }
class Box { public Size? Inner; public string Tag; }
class Order { public Box Box; public int Qty; }

class App
{
    static string Kind(Order o) => o switch
    {
        { Box.Inner.W: > 100 } => "wide",            // Size? -> Size
        { Box.Tag.Length: 0, Qty: 1 } => "untagged single",
        { Box.Tag: "gift" or "fragile" } => "special",
        { Box: null } => "no box",
        _ => "plain",
    };

    static void Main()
    {
        var big = new Size { W = 120, H = 3 };
        Order[] all =
        {
            new Order { Box = new Box { Inner = big, Tag = "x" } },
            new Order { Box = new Box { Tag = "" }, Qty = 1 },
            new Order { Box = new Box { Tag = "gift" } },
            new Order(),
            new Order { Box = new Box() },
        };
        foreach (Order o in all)
            Console.WriteLine(Kind(o));
        if (all[0] is { Box.Inner: { W: var w } inner, Qty: 0 })
            Console.WriteLine($"w={w} h={inner.H}");
    }
}
