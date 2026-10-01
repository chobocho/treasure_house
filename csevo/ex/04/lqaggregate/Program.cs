// 슬라이드 p4-v3-linq-aggregate — Aggregate 와 빈 시퀀스, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3, 4 };
        int product = xs.Aggregate((acc, x) => acc * x);
        string csv = xs.Aggregate("", (acc, x) =>
            acc.Length == 0 ? x.ToString() : acc + "," + x);
        Console.WriteLine(product + " | " + csv);

        int[] none = { };
        int seeded = none.Aggregate(0, (a, x) => a + x);
        Console.WriteLine("seeded: " + seeded);
        try
        {
            Console.WriteLine(none.Aggregate((a, x) => a + x));
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("unseeded: " + e.Message);
        }
    }
}
