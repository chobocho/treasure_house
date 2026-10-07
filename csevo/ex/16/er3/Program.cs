// 슬라이드 p16-eras-3 — 같은 프로그램 다섯 시대, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Order
{
    public string Customer { get; set; }
    public string Item { get; set; }
    public int Qty { get; set; }
    public int Price { get; set; }
    public int Total { get { return Qty * Price; } }
}

static class OrderExtensions
{
    public static int Big(this IEnumerable<Order> orders)
    {
        return orders.Count(o => o.Total >= 1000);
    }
}

static class Program
{
    const string Fmt = "{0,-6}{1,7}{2,7}{3,8}";

    static Order O(string c, string i, int q, int p)
    {
        return new Order { Customer = c, Item = i, Qty = q, Price = p };
    }

    static void Main()
    {
        var orders = new List<Order> {
            O("Ann", "pen", 3, 120), O("Bob", "ink", 1, 900),
            O("Ann", "pad", 2, 450), O("Cleo", "pen", 5, 120),
            O("Bob", "pen", 1, 120), O("Dan", "pad", 4, 450),
            O("Cleo", "ink", 2, 900), O("Ann", "ink", 1, 900),
            O("Eve", "ink", 2, 900),
        };
        var rows = (from o in orders
                    group o by o.Customer into g
                    let total = g.Sum(o => o.Total)
                    orderby total descending, g.Key
                    select new { Name = g.Key, Orders = g.Count(),
                                 Items = g.Sum(o => o.Qty),
                                 Total = total }).ToList();
        Console.WriteLine(Fmt, "name", "orders", "items", "total");
        foreach (var r in rows)
            Console.WriteLine(Fmt, r.Name, r.Orders, r.Items, r.Total);
        Console.WriteLine(Fmt, "TOTAL", rows.Sum(r => r.Orders),
            rows.Sum(r => r.Items), rows.Sum(r => r.Total));
        Console.WriteLine("big orders: {0}", orders.Big());
        var best = (from o in orders
                    group o.Qty by o.Item into g
                    orderby g.Sum() descending, g.Key
                    select new { Item = g.Key, Qty = g.Sum() }).First();
        Console.WriteLine("best item: {0} ({1})", best.Item, best.Qty);
    }
}
