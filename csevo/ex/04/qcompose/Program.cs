// 슬라이드 p4-v3-query-compose — 쿼리는 이어 붙이는 값, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<string> Search(string[] src, int minLen,
                                      bool sorted)
    {
        IEnumerable<string> q = from w in src select w;
        if (minLen > 0)
            q = from w in q where w.Length >= minLen select w;
        if (sorted)
            q = from w in q orderby w select w;
        return q;
    }

    static void Main()
    {
        string[] words = { "pear", "fig", "banana", "kiwi" };
        Console.WriteLine(string.Join(" ", Search(words, 0, false)));
        Console.WriteLine(string.Join(" ", Search(words, 4, false)));
        Console.WriteLine(string.Join(" ", Search(words, 4, true)));
    }
}
