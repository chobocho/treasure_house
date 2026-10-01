// 슬라이드 p4-v3-query-join-key — 여러 칸으로 join 하기, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var stock = new[] {
            new { Shop = "A", Item = "pen", Qty = 3 },
            new { Shop = "B", Item = "pen", Qty = 0 },
        };
        var orders = new[] {
            new { Store = "B", Item = "pen" },
            new { Store = "A", Item = "pen" },
        };

        var q = from o in orders
                join s in stock
                  on new { Shop = o.Store, o.Item }
                  equals new { s.Shop, s.Item }
                select o.Store + "/" + o.Item + " qty " + s.Qty;
        foreach (string line in q) Console.WriteLine(line);
    }
}
