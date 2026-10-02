// 슬라이드 p8-sum-c6 — 같은 프로그램을 C# 6 으로, C# 6
using System;

struct Item
{
    public string Name;
    public int Price;
    public Item(string n, int p) { Name = n; Price = p; }
}

class App
{
    static Tuple<int, int> MinMax(Item[] items)
    {
        int lo = int.MaxValue, hi = int.MinValue;
        foreach (var it in items)
        {
            lo = Math.Min(lo, it.Price);
            hi = Math.Max(hi, it.Price);
        }
        return Tuple.Create(lo, hi);          // an object on the heap
    }

    static int Dearest(Item[] items)          // an index, not a ref
    {
        int top = 0;
        for (int i = 1; i < items.Length; i++)
            if (items[i].Price > items[top].Price) top = i;
        return top;
    }

    static string Describe(object o)
    {
        if (o is int) return "int " + (int)o;
        var s = o as string;
        if (s != null) return "string of " + s.Length;
        return "other";
    }

    static void Main()
    {
        var items = new[] { new Item("pen", 1500), new Item("ink", 0),
                            new Item("pad", 4000) };
        int price;                            // declared up front
        if (int.TryParse("2500", out price)) items[1].Price = price;
        var mm = MinMax(items);
        Console.WriteLine(mm.Item1 + ".." + mm.Item2);
        int top = Dearest(items);
        items[top].Price -= 100;
        Console.WriteLine(items[top].Name + " " + items[top].Price);
        Console.WriteLine(Describe(42) + ", " + Describe("abc"));
    }
}
