// 슬라이드 p4-v3-linq-stable — OrderBy 는 안정 정렬, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        // 20 items, keys 0/1, numbered in source order
        List<KeyValuePair<int, int>> items =
            new List<KeyValuePair<int, int>>();
        for (int i = 0; i < 20; i++)
        {
            items.Add(new KeyValuePair<int, int>((i * 7) % 2, i));
        }

        var linq = items.OrderBy(p => p.Key).Select(p => p.Value);
        Console.WriteLine("OrderBy:   " + string.Join(" ", linq));

        List<KeyValuePair<int, int>> copy =
            new List<KeyValuePair<int, int>>(items);
        copy.Sort((a, b) => a.Key.CompareTo(b.Key));
        Console.WriteLine("List.Sort: "
            + string.Join(" ", copy.Select(p => p.Value)));
    }
}
