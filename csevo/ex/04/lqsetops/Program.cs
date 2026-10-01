// 슬라이드 p4-v3-linq-setops — Union·Intersect·Except 는 집합, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Show(string name, IEnumerable<int> xs)
    {
        Console.WriteLine(name.PadRight(11) + string.Join(" ", xs));
    }

    static void Main()
    {
        int[] a = { 1, 1, 2, 3, 3 };
        int[] b = { 3, 4 };

        Show("Concat", a.Concat(b));
        Show("Union", a.Union(b));
        Show("Intersect", a.Intersect(b));
        Show("Except", a.Except(b));
    }
}
