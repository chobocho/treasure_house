// 슬라이드 p12-v11-lp-why — 목록 패턴 이전과 이후, C# 11
using System;

class Program
{
    // C# 10: length test, then indexing by hand
    static string Old(int[] a)
    {
        if (a is null) return "null";
        if (a is { Length: 0 }) return "empty";
        if (a is { Length: >= 2 } && a[0] == 1 && a[^1] == 9)
            return "1 ... 9";
        if (a.Length == 1) return "one: " + a[0];
        return "other";
    }

    // C# 11: the shape is the pattern
    static string New(int[] a) => a switch
    {
        null => "null",
        [] => "empty",
        [1, .., 9] => "1 ... 9",
        [var x] => "one: " + x,
        _ => "other",
    };

    static void Main()
    {
        int[][] tests =
        {
            null, new int[0], new[] { 1, 5, 9 }, new[] { 1, 9 },
            new[] { 4 }, new[] { 9, 1 },
        };
        foreach (var t in tests)
            Console.WriteLine("{0,-8} {1}", Old(t), New(t));
    }
}
