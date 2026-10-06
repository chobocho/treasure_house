// 슬라이드 p13-v12-spread — 펼침 요소 ..e, C# 12
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<int> Evens(int n)
    {
        for (int i = 0; i < n; i++) yield return i * 2;
    }

    static void Main()
    {
        int[] row0 = [1, 2, 3];
        List<int> row1 = [4, 5];
        int[] all = [.. row0, .. row1, 6];      // array + list + 6
        int[] mix = [0, .. Evens(3), 9];        // an iterator
        int[] sq = [.. row0.Select(x => x * x)];
        Console.WriteLine(string.Join(",", all));
        Console.WriteLine(string.Join(",", mix));
        Console.WriteLine(string.Join(",", sq));
        List<int> copy = [.. all];
        copy.Add(7);
        Console.WriteLine(all.Length + " " + copy.Count);
#if BAD
        int[] bad = [.. 42];
#endif
    }
}
