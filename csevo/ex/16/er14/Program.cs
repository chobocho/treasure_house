// 슬라이드 p16-eras-14 — 같은 프로그램 다섯 시대, C# 14
using System;
using System.Collections.Generic;
using System.Linq;

Order[] orders =
[
    new("Ann", "pen", 3, 120), new("Bob", "ink", 1, 900),
    new("Ann", "pad", 2, 450), new("Cleo", "pen", 5, 120),
    new("Bob", "pen", 1, 120), new("Dan", "pad", 4, 450),
    new("Cleo", "ink", 2, 900), new("Ann", "ink", 1, 900),
    new("Eve", "ink", 2, 900),
];

List<Row> rows =
[
    .. orders.GroupBy(o => o.Customer)
        .Select(g => new Row(g.Key, g.Count(),
                             g.Sum(o => o.Qty), g.Sum(o => o.Total)))
        .OrderByDescending(r => r.Total)
        .ThenBy(r => r.Name, StringComparer.Ordinal)
];
Print("name", "orders", "items", "total");
foreach (var (name, count, items, total) in rows)
    Print(name, count, items, total);
Print("TOTAL", rows.Sum(r => r.Orders), rows.Sum(r => r.Items),
      rows.Sum(r => r.Total));
var best = orders.GroupBy(o => o.Item, o => o.Qty)
    .Select(g => (Item: g.Key, Qty: g.Sum()))
    .OrderByDescending(p => p.Qty)
    .ThenBy(p => p.Item, StringComparer.Ordinal).First();
Console.WriteLine($"""
    big orders: {orders.Big}
    best item: {best.Item} ({best.Qty})
    """);

static void Print(object a, object b, object c, object d)
    => Console.WriteLine($"{a,-6}{b,7}{c,7}{d,8}");

record Order(string Customer, string Item, int Qty, int Price)
{
    public int Total => Qty * Price;
}

record Row(string Name, int Orders, int Items, int Total);

static class OrderExtensions
{
    extension(IEnumerable<Order> orders)
    {
        public int Big => orders.Count(o => o.Total >= 1000);
    }
}
