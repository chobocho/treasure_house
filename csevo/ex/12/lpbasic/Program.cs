// 슬라이드 p12-v11-listpat — 목록 패턴, C# 11
using System;

class Program
{
    static string Show(int[] a) => a switch
    {
        [] => "empty",
        [var x] => "one: " + x,
        [1, 2, 3] => "exactly 1 2 3",
        [1, ..] => "starts with 1",
        [.., 0] => "ends with 0",
        [_, _] => "two items",
        _ => "other (" + a.Length + ")",
    };

    static void Main()
    {
        int[][] tests =
        {
            new int[0], new[] { 7 }, new[] { 1, 2, 3 },
            new[] { 1, 9, 9, 9 }, new[] { 5, 0 }, new[] { 5, 6 },
            new[] { 5, 6, 7 },
        };
        foreach (var t in tests)
            Console.WriteLine("[{0}] -> {1}",
                string.Join(", ", t), Show(t));

        object o = new[] { 1, 2, 3 };
        Console.WriteLine(o is int[] and [_, 2, _]);
    }
}
