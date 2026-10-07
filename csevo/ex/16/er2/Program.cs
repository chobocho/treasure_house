// 슬라이드 p16-eras-2 — 같은 프로그램 다섯 시대, C# 2.0
using System;
using System.Collections.Generic;

static class Program
{
    const string Fmt = "{0,-6}{1,7}{2,7}{3,8}";

    static void Main()
    {
        List<Order> orders = new List<Order>(Data.Orders());
        Dictionary<string, Row> byName = new Dictionary<string, Row>();
        Dictionary<string, int> byItem = new Dictionary<string, int>();
        foreach (Order o in orders)
        {
            Row r;
            if (!byName.TryGetValue(o.Customer, out r))
            {
                r = new Row(o.Customer);
                byName.Add(o.Customer, r);
            }
            r.Orders++; r.Items += o.Qty; r.Total += o.Total;
            int q;
            byItem.TryGetValue(o.Item, out q);
            byItem[o.Item] = q + o.Qty;
        }
        List<Row> rows = new List<Row>(byName.Values);
        rows.Sort(delegate(Row a, Row b)
        {
            if (a.Total != b.Total) return b.Total - a.Total;
            return string.CompareOrdinal(a.Name, b.Name);
        });
        Console.WriteLine(Fmt, "name", "orders", "items", "total");
        Row t = new Row("TOTAL");
        foreach (Row r in rows)
        {
            Console.WriteLine(Fmt, r.Name, r.Orders, r.Items, r.Total);
            t.Orders += r.Orders; t.Items += r.Items;
            t.Total += r.Total;
        }
        Console.WriteLine(Fmt, t.Name, t.Orders, t.Items, t.Total);
        List<Order> big = orders.FindAll(
            delegate(Order o) { return o.Total >= 1000; });
        Console.WriteLine("big orders: {0}", big.Count);
        KeyValuePair<string, int> best =
            new KeyValuePair<string, int>();
        foreach (KeyValuePair<string, int> e in byItem)
            if (e.Value > best.Value || (e.Value == best.Value
                && string.CompareOrdinal(e.Key, best.Key) < 0))
                best = e;
        Console.WriteLine("best item: {0} ({1})", best.Key, best.Value);
    }
}
