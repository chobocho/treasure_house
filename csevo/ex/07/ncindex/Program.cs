// 슬라이드 p7-v6-nullcond-index — ?[] 원소 접근, C# 6.0
using System;
using System.Collections.Generic;

class App
{
    static void Show(int[] a, List<string> l,
        Dictionary<string, int> d)
    {
        int? first = a?[0];
        string name = l?[0];
        int? count = d?["k"];
        Console.WriteLine("[{0}] [{1}] [{2}] len={3}",
            first, name, count, a?.Length ?? -1);
    }

    static void Main()
    {
        Show(new[] { 7, 8 }, new List<string> { "x" },
            new Dictionary<string, int> { { "k", 3 } });
        Show(null, null, null);
        try { Show(new int[0], null, null); }
        catch (IndexOutOfRangeException)
        { Console.WriteLine("?[] guards null only, not the index"); }
    }
}
