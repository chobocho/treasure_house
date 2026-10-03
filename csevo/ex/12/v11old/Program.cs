// 슬라이드 p12-sum-old — 같은 프로그램의 C# 10 판, C# 10
using System;
using System.Text;

class Item
{
    public Item(string name, int[] qty) { Name = name; Qty = qty; }
    public string Name { get; init; }
    public int[] Qty { get; init; }
}

static class Report
{
    public static int Sum(int[] xs)
    {
        int s = 0;
        foreach (int x in xs) s += x;
        return s;
    }

    public static double Sum(double[] xs)
    {
        double s = 0;
        foreach (double x in xs) s += x;
        return s;
    }

    public static string Kind(int[] q) => q switch
    {
        { Length: 0 } => "empty",
        { Length: 1 } => "single " + q[0],
        { Length: >= 2 } when q[^1] > 100 => "big last",
        _ => "lines " + q.Length,
    };
}

class Program
{
    static void Main()
    {
        Console.WriteLine("name | kind     | total\n"
            + "-----+----------+------");
        Item[] items =
        {
            new Item("a", new int[0]),
            new Item("b", new[] { 7 }),
            new Item("c", new[] { 1, 2, 500 }),
            new Item("d", new[] { 3, 4 }),
        };
        foreach (Item it in items)
            Console.WriteLine($"{it.Name,-4} | {Report.Kind(it.Qty),-8}"
                + $" | {Report.Sum(it.Qty)}");
        Console.WriteLine(Report.Sum(new[] { 1.5, 2.25 }));
        Console.WriteLine("UTF-8 bytes: "
            + Encoding.UTF8.GetByteCount("héllo"));
    }
}
