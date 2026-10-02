// 슬라이드 p8-sum-c73 — 같은 프로그램을 C# 7.3 으로, C# 7.3
using System;

readonly struct Item
{
    public readonly string Name;
    public readonly int Price;
    public Item(string n, int p) { Name = n; Price = p; }
    public Item WithPrice(int p) => new Item(Name, p);
}

class App
{
    static (int lo, int hi) MinMax(ReadOnlySpan<Item> items)
    {
        int lo = int.MaxValue, hi = int.MinValue;
        foreach (ref readonly Item it in items)    // no copies
        {
            lo = Math.Min(lo, it.Price);
            hi = Math.Max(hi, it.Price);
        }
        return (lo, hi);                           // a ValueTuple
    }

    static ref Item Dearest(Item[] items)    // a ref, not an index
    {
        ref Item top = ref items[0];
        for (int i = 1; i < items.Length; i++)
            if (items[i].Price > top.Price)
                top = ref items[i];
        return ref top;
    }

    static string Describe(object o)
    {
        switch (o)
        {
            case int n: return "int " + n;
            case string s: return "string of " + s.Length;
            default: return "other";
        }
    }

    static void Main()
    {
        var items = new[] { new Item("pen", 1_500), new Item("ink", 0),
                            new Item("pad", 4_000) };
        if (int.TryParse("2500", out var price))
            items[1] = items[1].WithPrice(price);
        var (lo, hi) = MinMax(items);
        Console.WriteLine(lo + ".." + hi);
        ref Item top = ref Dearest(items);
        top = top.WithPrice(top.Price - 100);
        Console.WriteLine($"{top.Name} {top.Price}");
        Console.WriteLine(Describe(42) + ", " + Describe("abc"));
    }
}
