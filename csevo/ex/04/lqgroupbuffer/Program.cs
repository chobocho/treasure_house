// 슬라이드 p4-v3-linq-groupby — GroupBy 와 ToLookup, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<int> Src()
    {
        for (int i = 1; i <= 4; i++)
        {
            Console.WriteLine("  pull " + i);
            yield return i;
        }
    }

    static void Main()
    {
        IEnumerable<IGrouping<bool, int>> g =
            Src().GroupBy(x => x % 2 == 0);
        Console.WriteLine("GroupBy built");
        foreach (IGrouping<bool, int> grp in g)
        {
            Console.WriteLine("even=" + grp.Key + ": "
                              + string.Join(" ", grp));
        }

        ILookup<bool, int> l = Src().ToLookup(x => x % 2 == 0);
        Console.WriteLine("ToLookup built, " + l.Count + " keys");
        Console.WriteLine("even=True: " + string.Join(" ", l[true]));
    }
}
