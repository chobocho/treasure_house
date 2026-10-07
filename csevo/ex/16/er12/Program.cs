// 슬라이드 p16-eras-12 — 같은 프로그램 다섯 시대, C# 1.2
using System;
using System.Collections;

class Program
{
    const string Fmt = "{0,-6}{1,7}{2,7}{3,8}";

    static ArrayList MakeOrders()
    {
        ArrayList list = new ArrayList();
        list.Add(new Order("Ann", "pen", 3, 120));
        list.Add(new Order("Bob", "ink", 1, 900));
        list.Add(new Order("Ann", "pad", 2, 450));
        list.Add(new Order("Cleo", "pen", 5, 120));
        list.Add(new Order("Bob", "pen", 1, 120));
        list.Add(new Order("Dan", "pad", 4, 450));
        list.Add(new Order("Cleo", "ink", 2, 900));
        list.Add(new Order("Ann", "ink", 1, 900));
        list.Add(new Order("Eve", "ink", 2, 900));
        return list;
    }

    static bool IsBig(Order o) { return o.Total >= 1000; }

    static int Count(ArrayList orders, OrderTest test)
    {
        int n = 0;
        foreach (Order o in orders)
            if (test(o)) n++;
        return n;
    }

    static void Main()
    {
        ArrayList orders = MakeOrders();
        Hashtable byName = new Hashtable();
        Hashtable byItem = new Hashtable();
        foreach (Order o in orders)
        {
            Row r = (Row) byName[o.Customer];
            if (r == null)
            {
                r = new Row(o.Customer);
                byName[o.Customer] = r;
            }
            r.Orders++; r.Items += o.Qty; r.Total += o.Total;
            object q = byItem[o.Item];
            byItem[o.Item] = (q == null ? 0 : (int) q) + o.Qty;
        }
        ArrayList rows = new ArrayList(byName.Values);
        rows.Sort(new ByTotal());
        Console.WriteLine(Fmt, "name", "orders", "items", "total");
        Row t = new Row("TOTAL");
        foreach (Row r in rows)
        {
            Console.WriteLine(Fmt, r.Name, r.Orders, r.Items, r.Total);
            t.Orders += r.Orders; t.Items += r.Items;
            t.Total += r.Total;
        }
        Console.WriteLine(Fmt, t.Name, t.Orders, t.Items, t.Total);
        Console.WriteLine("big orders: {0}",
            Count(orders, new OrderTest(IsBig)));
        string best = null;
        int bestQty = 0;
        foreach (DictionaryEntry e in byItem)
        {
            string item = (string) e.Key;
            int qty = (int) e.Value;
            if (qty > bestQty || (qty == bestQty
                && String.CompareOrdinal(item, best) < 0))
            {
                best = item; bestQty = qty;
            }
        }
        Console.WriteLine("best item: {0} ({1})", best, bestQty);
    }
}
