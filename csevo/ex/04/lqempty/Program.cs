// 슬라이드 p4-v3-linq-empty — 빈 시퀀스의 Sum·Max·Average, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Show(string name, Func<object> f)
    {
        try
        {
            object r = f();
            Console.WriteLine(name + " = " + (r == null ? "null" : r));
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(name + " -> " + e.Message);
        }
    }

    static void Main()
    {
        int[] none = { };
        int?[] maybe = { };

        Show("Sum", () => none.Sum());
        Show("Max", () => none.Max());
        Show("Average", () => none.Average());
        Show("Max of int?", () => maybe.Max());
        Show("Average of int?", () => maybe.Average());
    }
}
