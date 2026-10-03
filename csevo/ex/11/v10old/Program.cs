// 슬라이드 p11-sum-old — 같은 프로그램을 C# 9.0 으로, C# 9.0
using System;
using System.Linq;

namespace Shop
{
    record Item(string Name, decimal Price, Tag Tag);
    record Tag(string Kind);

    static class App
    {
        const string Unit = "KRW";
        const string Header = "price (" + Unit + ")";

        static void Main()
        {
            var items = new[]
            {
                new Item("pen", 1200m, new("office")),
                new Item("tea", 3000m, new("food")),
            };
            Func<Item, bool> cheap = i => i.Price < 2000m;
            Console.WriteLine(Header);
            foreach (var it in items)
            {
                string label = it switch
                {
                    { Tag: { Kind: "food" } } => "food",
                    _ when cheap(it) => "cheap",
                    _ => "other",
                };
                Console.WriteLine($"{it.Name,-4} {it.Price,6} {label}");
            }
            var d = items[0] with { Price = 1000m };
            var (count, sum) = (items.Length, items.Sum(i => i.Price));
            Console.WriteLine($"{d.Name} {d.Price} {count} {sum}");
        }
    }
}
