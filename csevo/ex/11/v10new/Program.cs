// 슬라이드 p11-sum-new — 같은 프로그램을 C# 10 으로, C# 10.0
global using System;
global using System.Linq;

namespace Shop;

record struct Item(string Name, decimal Price, Tag Tag);
record Tag(string Kind);

static class App
{
    const string Unit = "KRW";
    const string Header = $"price ({Unit})";

    static void Main()
    {
        var items = new[]
        {
            new Item("pen", 1200m, new("office")),
            new Item("tea", 3000m, new("food")),
        };
        var cheap = (Item i) => i.Price < 2000m;
        Console.WriteLine(Header);
        foreach (var it in items)
        {
            string label = it switch
            {
                { Tag.Kind: "food" } => "food",
                _ when cheap(it) => "cheap",
                _ => "other",
            };
            Console.WriteLine($"{it.Name,-4} {it.Price,6} {label}");
        }
        var d = items[0] with { Price = 1000m };
        int count;
        (count, var sum) = (items.Length, items.Sum(i => i.Price));
        Console.WriteLine($"{d.Name} {d.Price} {count} {sum}");
    }
}
