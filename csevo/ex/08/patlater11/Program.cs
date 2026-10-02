// 슬라이드 p8-v7-pat-later11 — 목록 패턴, C# 11.0
using System;

class App
{
    static string M(int[] a) => a switch
    {
        [] => "empty",
        [var only] => "one: " + only,
        [1, .., var last] => "starts with 1, ends with " + last,
        _ => "other",
    };

    static void Main()
    {
        Console.WriteLine(M(new int[0]));
        Console.WriteLine(M(new[] { 7 }));
        Console.WriteLine(M(new[] { 1, 2, 3 }));
        Console.WriteLine(M(new[] { 2, 3 }));
    }
}
