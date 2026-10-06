// 슬라이드 p13-v12-ce-patterns — 가르고 다시 짓기, C# 12
using System;

class Program
{
    static int[] Rev(int[] xs) =>
        xs is [var head, .. var tail] ? [.. Rev(tail), head] : [];

    static int[] Merge(int[] a, int[] b) => (a, b) switch
    {
        ([], _) => b,
        (_, []) => a,
        ([var x, .. var xs], [var y, ..]) when x <= y =>
            [x, .. Merge(xs, b)],
        (_, [var y, .. var ys]) => [y, .. Merge(a, ys)],
    };

    static void Main()
    {
        Console.WriteLine(string.Join(",", Rev([1, 2, 3, 4])));
        Console.WriteLine(string.Join(",",
            Merge([1, 4, 9], [2, 3, 10])));
    }
}
