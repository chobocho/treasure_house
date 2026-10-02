// 슬라이드 p10-v9-pat-later — C# 9 패턴과 뒤 버전의 패턴, C# 11.0
using System;

class Order
{
    public string Name;
    public int[] Qty;
}

class App
{
    static string Check(Order o) => o switch
    {
        { Name.Length: > 8 } => "long name",            // C# 10
        { Qty: [] } => "no lines",                       // C# 11
        { Qty: [> 0 and <= 10, ..] } => "first 1..10",
        { Qty: [.., < 0] } => "last negative",
        _ => "other",
    };

    static void Main()
    {
        Console.WriteLine(Check(new Order { Name = "very long name" }));
        int[][] all = { new int[0], new[] { 3, 9 }, new[] { 0, -1 } };
        foreach (int[] q in all)
            Console.WriteLine(Check(new Order { Name = "x", Qty = q }));
    }
}
