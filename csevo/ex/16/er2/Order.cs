// 슬라이드 p16-eras-2 — 같은 프로그램 다섯 시대, C# 2.0
using System.Collections.Generic;

class Order
{
    public string Customer;
    public string Item;
    public int Qty;
    public int Price;

    public Order(string customer, string item, int qty, int price)
    {
        Customer = customer; Item = item; Qty = qty; Price = price;
    }

    public int Total { get { return Qty * Price; } }
}

class Row
{
    public string Name;
    public int Orders, Items, Total;

    public Row(string name) { Name = name; }
}

static class Data
{
    public static IEnumerable<Order> Orders()
    {
        yield return new Order("Ann", "pen", 3, 120);
        yield return new Order("Bob", "ink", 1, 900);
        yield return new Order("Ann", "pad", 2, 450);
        yield return new Order("Cleo", "pen", 5, 120);
        yield return new Order("Bob", "pen", 1, 120);
        yield return new Order("Dan", "pad", 4, 450);
        yield return new Order("Cleo", "ink", 2, 900);
        yield return new Order("Ann", "ink", 1, 900);
        yield return new Order("Eve", "ink", 2, 900);
    }
}
