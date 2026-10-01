// 슬라이드 p4-v3-linq-capture — 값은 돌 때 읽는다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3, 4, 5 };
        int min = 2;

        IEnumerable<int> q = xs.Where(x => x > min);
        min = 4;
        Console.WriteLine(string.Join(" ", q));

        min = 0;
        Console.WriteLine(string.Join(" ", q));
    }
}
