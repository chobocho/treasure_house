// 슬라이드 p4-v3-linq-first — First·FirstOrDefault·Single, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Show(string name, Func<object> f)
    {
        try
        {
            Console.WriteLine(name + " = " + f());
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(name + " -> " + e.Message);
        }
    }

    static void Main()
    {
        int[] xs = { 0, 4, 6 };

        Show("First(>5)", () => xs.First(x => x > 5));
        Show("First(>9)", () => xs.First(x => x > 9));
        Show("FirstOrDefault(>9)", () => xs.FirstOrDefault(x => x > 9));
        Show("FirstOrDefault(<1)", () => xs.FirstOrDefault(x => x < 1));
        Show("Single(>3)", () => xs.Single(x => x > 3));
        Show("Single(>5)", () => xs.Single(x => x > 5));
        Show("DefaultIfEmpty(-1)",
             () => xs.Where(x => x > 9).DefaultIfEmpty(-1).First());
    }
}
