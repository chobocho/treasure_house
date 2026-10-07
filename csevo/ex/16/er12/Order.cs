// 슬라이드 p16-eras-12 — 같은 프로그램 다섯 시대, C# 1.2
using System;
using System.Collections;

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

// total descending, then name (ordinal): no two rows compare equal
class ByTotal : IComparer
{
    public int Compare(object x, object y)
    {
        Row a = (Row) x, b = (Row) y;
        if (a.Total != b.Total) return b.Total - a.Total;
        return String.CompareOrdinal(a.Name, b.Name);
    }
}

delegate bool OrderTest(Order o);
