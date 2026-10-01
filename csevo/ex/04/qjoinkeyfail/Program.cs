// 슬라이드 p4-v3-query-join-keyfail — 키의 속성 이름이 다르면, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var stock = new[] { new { Shop = "A", Item = "pen", Qty = 3 } };
        var orders = new[] { new { Store = "A", Item = "pen" } };

        var q = from o in orders
                join s in stock
                  on new { o.Store, o.Item }
                  equals new { s.Shop, s.Item }
                select s.Qty;
        Console.WriteLine(q.Count());
    }
}
