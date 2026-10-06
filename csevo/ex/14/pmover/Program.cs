// 슬라이드 p14-v13-pm-over — 배열과 스팬 params 가 함께면, C# 13
using System;
using System.Collections.Generic;

class Program
{
    static string M(params int[] xs) => "int[]";
    static string M(params ReadOnlySpan<int> xs) => "ReadOnlySpan";

    static string N(params Span<int> xs) => "Span";
    static string N(params ReadOnlySpan<int> xs) => "ReadOnlySpan";

    static string P(params IEnumerable<int> xs) => "IEnumerable";
    static string P(params List<int> xs) => "List";

    static void Main()
    {
        int[] arr = { 1, 2 };
        Console.WriteLine("M(1, 2, 3) " + M(1, 2, 3));
        Console.WriteLine("M()        " + M());
        Console.WriteLine("M(arr)     " + M(arr));
        Console.WriteLine("M([1, 2])  " + M([1, 2]));
        Console.WriteLine("N(1, 2, 3) " + N(1, 2, 3));
        Console.WriteLine("P(1, 2, 3) " + P(1, 2, 3));
    }
}
