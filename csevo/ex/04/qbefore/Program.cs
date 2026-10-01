// 슬라이드 p4-v3-query-why — 쿼리 식 이전의 거르기·정렬·바꾸기, C# 2.0
using System;
using System.Collections.Generic;

class Program
{
    static int ByLength(string a, string b)
    {
        return a.Length.CompareTo(b.Length);
    }

    static void Main()
    {
        string[] words = { "melon", "fig", "banana",
                           "kiwi", "cherries" };

        List<string> found = new List<string>();
        foreach (string w in words)
        {
            if (w.Length > 3) found.Add(w);
        }
        found.Sort(ByLength);

        List<string> result = new List<string>();
        foreach (string w in found)
        {
            result.Add(w.ToUpper());
        }
        Console.WriteLine(string.Join(" ", result.ToArray()));
    }
}
