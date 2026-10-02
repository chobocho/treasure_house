// 슬라이드 p7-v6-wrap-c5 — 같은 클래스를 C# 5 로, C# 5
using System;
using System.Collections.Generic;

class Item
{
    readonly string name;
    readonly decimal price;
    readonly Dictionary<string, int> stock =
        new Dictionary<string, int> { { "Seoul", 3 }, { "Busan", 0 } };
    public Item(string name, decimal price)
    {
        this.name = name;
        this.price = price;
    }

    public string Name { get { return name; } }
    public decimal Price { get { return price; } }

    public decimal Total(int n) { return Math.Round(price * n, 2); }
    public bool InStock(string city) { return stock[city] > 0; }
    public override string ToString() { return name + " " + price; }
}

class Program
{
    static void Main()
    {
        Item tea = new Item("tea", 1.25m);
        Console.WriteLine(tea + " x3 = " + tea.Total(3));
        foreach (string city in new[] { "Seoul", "Busan", "Jeju" })
        {
            try { Console.WriteLine(city + ": " + tea.InStock(city)); }
            catch (KeyNotFoundException)
            {
                if (!city.StartsWith("J")) throw;
                Console.WriteLine(city + ": no store");
            }
        }
    }
}
