// 슬라이드 p7-v6-wrap-c6 — 같은 클래스를 C# 6 으로, C# 6.0
using System;
using System.Collections.Generic;
using static System.Math;

class Item
{
    public string Name { get; }
    public decimal Price { get; }
    Dictionary<string, int> Stock { get; } =
        new Dictionary<string, int> { ["Seoul"] = 3, ["Busan"] = 0 };

    public Item(string name, decimal price)
    {
        Name = name;
        Price = price;
    }

    public decimal Total(int n) => Round(Price * n, 2);
    public bool InStock(string city) => Stock[city] > 0;
    public override string ToString() => Name + " " + Price;
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
            catch (KeyNotFoundException) when (city.StartsWith("J"))
            {
                Console.WriteLine(city + ": no store");
            }
        }
    }
}
