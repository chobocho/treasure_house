// 슬라이드 p4-v3-query-end — select 나 group 으로 끝나야 한다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3 };
        IEnumerable<int> q = from x in xs
                             where x > 1;
        Console.WriteLine(q.Count());
    }
}
