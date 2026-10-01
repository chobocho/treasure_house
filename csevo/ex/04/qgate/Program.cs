// 슬라이드 p4-v3-query-gate — 쿼리 식, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] words = { "melon", "fig", "banana",
                           "kiwi", "cherries" };

        IEnumerable<string> result =
            from w in words
            where w.Length > 3
            orderby w.Length
            select w.ToUpper();

        Console.WriteLine(string.Join(" ", result));
    }
}
