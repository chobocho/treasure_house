// 슬라이드 p4-v3-linq-deferred-exc — 예외는 쿼리를 돌릴 때 난다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 2, 1, 0 };
        IEnumerable<int> q = xs.Select(x => 10 / x);
        Console.WriteLine("query built");

        foreach (int y in q)
        {
            Console.WriteLine(y);
        }
    }
}
