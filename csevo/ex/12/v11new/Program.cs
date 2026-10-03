// 슬라이드 p12-sum-new — 12부의 기능을 한 프로그램에, C# 11
using System;
using System.Numerics;

class Item
{
    public required string Name { get; init; }
    public required int[] Qty { get; init; }
}

file static class Report
{
    public static T Sum<T>(T[] xs) where T : INumber<T>
    {
        T s = T.Zero;
        foreach (T x in xs) s += x;
        return s;
    }

    public static string Kind(int[] q) => q switch
    {
        [] => "empty",
        [var one] => "single " + one,
        [_, .., > 100] => "big last",
        _ => "lines " + q.Length,
    };
}

class Program
{
    static void Main()
    {
        Console.WriteLine("""
            name | kind     | total
            -----+----------+------
            """);
        Item[] items =
        {
            new Item { Name = "a", Qty = new int[0] },
            new Item { Name = "b", Qty = new[] { 7 } },
            new Item { Name = "c", Qty = new[] { 1, 2, 500 } },
            new Item { Name = "d", Qty = new[] { 3, 4 } },
        };
        foreach (Item it in items)
            Console.WriteLine($"{it.Name,-4} | {Report.Kind(it.Qty),-8}"
                + $" | {Report.Sum(it.Qty)}");
        Console.WriteLine(Report.Sum(new[] { 1.5, 2.25 }));
        Console.WriteLine("UTF-8 bytes: " + "héllo"u8.Length);
    }
}
