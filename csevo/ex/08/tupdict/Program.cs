// 슬라이드 p8-v7-tuple-dict — 여러 칸 열쇠, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        // a dictionary with a two-part key
        var seats = new Dictionary<(int row, char col), string>();
        seats[(1, 'A')] = "Kim";
        seats[(1, 'B')] = "Lee";
        seats[(1, 'A')] = "Park";           // same key: replaced
        Console.WriteLine(seats.Count);
        Console.WriteLine(seats[(1, 'A')]);
        Console.WriteLine(seats.ContainsKey((2, 'A')));

        var seen = new HashSet<(string, int)>();
        Console.WriteLine(seen.Add(("a", 1)));
        Console.WriteLine(seen.Add(("a", 1)));  // equal: not added
        var list = new List<(string, int)> { ("b", 2), ("a", 1) };
        Console.WriteLine(list.IndexOf(("a", 1)));
    }
}
