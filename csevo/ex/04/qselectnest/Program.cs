// 슬라이드 p4-v3-query-nested — select 는 펴 주지 않는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] lines = { "a b", "c d e" };

        IEnumerable<string[]> nested = from l in lines
                                       select l.Split(' ');
        IEnumerable<string> flat = from l in lines
                                   from w in l.Split(' ')
                                   select w;

        Console.WriteLine(nested.Count() + " vs " + flat.Count());
        foreach (string[] a in nested) Console.WriteLine(a);
        Console.WriteLine(string.Join(" ", flat));
    }
}
