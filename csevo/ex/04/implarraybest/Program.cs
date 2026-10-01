// 슬라이드 p4-v3-implarray-best — 가장 좋은 공통 형식, C# 3.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(new[] { 1, 2 }.GetType());
        Console.WriteLine(new[] { 1, 2.5 }.GetType());
        Console.WriteLine(new[] { 1L, 2 }.GetType());
        Console.WriteLine(new[] { "a", null }.GetType());
        Console.WriteLine(new[] { 1, (int?)null }.GetType());
        Console.WriteLine(new[,] { { 1, 2 }, { 3, 4 } }.GetType());
    }
}
