// 슬라이드 p7-v6-interp-newline11 — 구멍 안의 줄바꿈, C# 11.0
using System;
using System.Linq;

class App
{
    static void Main()
    {
        int[] xs = { 3, 1, 2 };
        Console.WriteLine($"sorted: {string.Join(",",
            xs.OrderBy(x => x))}, max: {xs
            .Max()}");
    }
}
