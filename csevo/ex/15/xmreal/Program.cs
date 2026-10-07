// 슬라이드 p15-v14-xm-real — 확장 멤버로 만든 작은 장바구니, C# 14
using System;
using System.Collections.Generic;
using System.Linq;

record Item(string Name, decimal Price, int Qty);

static class CartExt
{
    extension(IReadOnlyList<Item> cart)
    {
        public bool IsEmpty => cart.Count == 0;
        public decimal Total => cart.Sum(i => i.Price * i.Qty);
        public IEnumerable<Item> Over(decimal p) =>
            cart.Where(i => i.Price > p);
    }

    extension(IReadOnlyList<Item>)
    {
        public static IReadOnlyList<Item> Empty => Array.Empty<Item>();
        public static IReadOnlyList<Item> operator +(
            IReadOnlyList<Item> a, IReadOnlyList<Item> b) =>
            a.Concat(b).ToList();
    }

    extension(decimal d)
    {
        public string Won => d.ToString("N0") + "원";
    }
}

class Program
{
    static void Main()
    {
        IReadOnlyList<Item> a =
            [new("pen", 1200m, 3), new("ink", 800m, 2)];
        IReadOnlyList<Item> b = [new("pad", 4500m, 1)];
        var cart = IReadOnlyList<Item>.Empty + a + b;
        Console.WriteLine(cart.Count + " " + cart.IsEmpty
            + " " + cart.Total.Won);
        var big = cart.Over(1000m).Select(i => i.Name);
        Console.WriteLine(string.Join(",", big));
    }
}
