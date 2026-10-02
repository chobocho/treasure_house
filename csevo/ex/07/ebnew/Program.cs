// 슬라이드 p7-v6-eb-new — => new 가 만드는 사라지는 컬렉션, C# 6.0
using System;
using System.Collections.Generic;

class Order
{
    // a new list on every read
    public List<string> Lines => new List<string>();
    // one list, created with the object
    public List<string> Items { get; } = new List<string>();
}

class Program
{
    static void Main()
    {
        Order o = new Order();
        o.Lines.Add("tea");
        o.Items.Add("tea");
        Console.WriteLine("Lines: " + o.Lines.Count);
        Console.WriteLine("Items: " + o.Items.Count);
        Console.WriteLine(ReferenceEquals(o.Lines, o.Lines));
        Console.WriteLine(ReferenceEquals(o.Items, o.Items));
    }
}
