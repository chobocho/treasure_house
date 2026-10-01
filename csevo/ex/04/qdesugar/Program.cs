// 슬라이드 p4-v3-query-translate — 쿼리 식과 손으로 옮긴 호출, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] words = { "melon", "fig", "banana",
                           "kiwi", "cherries" };

        IEnumerable<string> q1 =
            from w in words
            where w.Length > 3
            orderby w.Length descending, w
            select w.ToUpper();

        // the translation of 12.22.3, written by hand
        IEnumerable<string> q2 = words
            .Where(w => w.Length > 3)
            .OrderByDescending(w => w.Length)
            .ThenBy(w => w)
            .Select(w => w.ToUpper());

        Console.WriteLine(string.Join(" ", q1));
        Console.WriteLine(string.Join(" ", q2));
        Console.WriteLine(q1.SequenceEqual(q2));
    }
}
