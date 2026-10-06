// 슬라이드 p14-v13-pm-forms — 정상 꼴과 확장 꼴, C# 13
using System;
using System.Collections.Generic;

class Program
{
    static List<object> list = new() { 1, 2 };

    static string E(params IEnumerable<object> xs) =>
        xs == null ? "null" : ReferenceEquals(xs, list) ? "list itself"
        : xs.GetType().Name;

    static string S(params ReadOnlySpan<string> xs) =>
        "Length=" + xs.Length + (xs.Length > 0 && xs[0] == null
            ? " [0]=null" : "");

    static void Main()
    {
        Console.WriteLine("E(list)         " + E(list));
        Console.WriteLine("E((object)list) " + E((object)list));
        Console.WriteLine("E([.. list])    " + E([.. list]));
        Console.WriteLine("E(null)         " + E(null));
        Console.WriteLine("S(null)         " + S(null));
        Console.WriteLine("S((string)null) " + S((string)null));
        Console.WriteLine("S()             " + S());
    }
}
