// 슬라이드 p9-v8-pat-list11 — 목록 패턴, C# 11
using System;

class App
{
    static string Shape(int[] a) => a switch
    {
        [] => "empty",
        [var x] => "one: " + x,
        [0, ..] => "starts with 0",
        [.., var last] when last < 0 => "ends negative",
        [var first, .. var mid, var last] =>
            $"{first}..{last} ({mid.Length} between)",
    };

    static void Main()
    {
        Console.WriteLine(Shape(new int[0]));
        Console.WriteLine(Shape(new[] { 5 }));
        Console.WriteLine(Shape(new[] { 0, 1, 2 }));
        Console.WriteLine(Shape(new[] { 3, -1 }));
        Console.WriteLine(Shape(new[] { 1, 2, 3, 4 }));
    }
}
