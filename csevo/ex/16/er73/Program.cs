// 슬라이드 p16-eras-73 — 같은 프로그램 다섯 시대, C# 7.3
using System;
using System.Collections.Generic;
using System.Linq;

static class Program
{
    static void Main()
    {
        (string Customer, string Item, int Qty, int Price)[] orders =
        {
            ("Ann", "pen", 3, 120), ("Bob", "ink", 1, 900),
            ("Ann", "pad", 2, 450), ("Cleo", "pen", 5, 120),
            ("Bob", "pen", 1, 120), ("Dan", "pad", 4, 450),
            ("Cleo", "ink", 2, 900), ("Ann", "ink", 1, 900),
            ("Eve", "ink", 2, 900),
        };
        int Total((string, string, int Qty, int Price) o)
            => o.Qty * o.Price;
        void Print(object a, object b, object c, object d)
            => Console.WriteLine($"{a,-6}{b,7}{c,7}{d,8}");

        var rows = orders.GroupBy(o => o.Customer)
            .Select(g => (Name: g.Key, Orders: g.Count(),
                Items: g.Sum(o => o.Qty), Total: g.Sum(Total)))
            .OrderByDescending(r => r.Total)
            .ThenBy(r => r.Name, StringComparer.Ordinal)
            .ToList();
        Print("name", "orders", "items", "total");
        foreach (var (name, count, items, total) in rows)
            Print(name, count, items, total);
        Print("TOTAL", rows.Sum(r => r.Orders), rows.Sum(r => r.Items),
              rows.Sum(r => r.Total));
        var big = orders.Count(o => Total(o) >= 1000);
        Console.WriteLine($"big orders: {big}");

        var qty = new Dictionary<string, int>();
        foreach (var (_, item, q, _) in orders)
            qty[item] = q + (qty.TryGetValue(item, out var n) ? n : 0);
        var best = qty.OrderByDescending(p => p.Value)
            .ThenBy(p => p.Key, StringComparer.Ordinal).First();
        Console.WriteLine($"best item: {best.Key} ({best.Value})");
    }
}
