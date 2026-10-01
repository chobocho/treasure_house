// 슬라이드 p4-v3-linq-buffer — OrderBy 는 먼저 다 읽는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<int> Src()
    {
        foreach (int i in new int[] { 3, 1, 2 })
        {
            Console.WriteLine("  pull " + i);
            yield return i;
        }
    }

    static void Main()
    {
        Console.WriteLine("Where:");
        foreach (int x in Src().Where(v => v > 0))
        {
            Console.WriteLine("got " + x);
            break;
        }

        Console.WriteLine("OrderBy:");
        foreach (int x in Src().OrderBy(v => v))
        {
            Console.WriteLine("got " + x);
            break;
        }
    }
}
