// 슬라이드 p8-v7_1-tuplenames — 튜플 원소 이름 유추, C# 7.1
using System;
using System.Linq;

class Item
{
    public string Name;
    public int Price;
}

class App
{
    static void Main()
    {
        int count = 5;
        string label = "Colors used in the map";
        var pair = (count, label);           // names: count, label
        Console.WriteLine(pair.count + " " + pair.label.Length);

        var items = new[] { new Item { Name = "pen", Price = 3 },
                            new Item { Name = "ink", Price = 7 } };
        Item none = null;
        var t = (items[0].Name, none?.Price); // names: Name, Price
        Console.WriteLine(t.Name + " " + t.Price.HasValue);

        var cheap = items.Select(i => (i.Name, i.Price))
                         .Where(x => x.Price < 5);
        foreach (var x in cheap)
            Console.WriteLine(x.Name + " " + x.Price);
    }
}
