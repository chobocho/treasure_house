// 슬라이드 p4-v3-linq-deferred — Where 는 부를 때 돌지 않는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static bool IsOdd(int x)
    {
        Console.WriteLine("  test " + x);
        return x % 2 == 1;
    }

    static void Main()
    {
        int[] xs = { 1, 2, 3 };

        IEnumerable<int> q = xs.Where(IsOdd);
        Console.WriteLine("query built");

        foreach (int y in q)
        {
            Console.WriteLine("got " + y);
        }
    }
}
