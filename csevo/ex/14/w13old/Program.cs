// 슬라이드 p14-sum-old — 같은 프로그램의 C# 12 판, C# 12
using System;
using System.Collections.Generic;

class Report
{
    public string Tag => "\u001b[1mC#\u001b[0m";
    public int[] Last { get; } = new int[3];
}

static class Fmt
{
    static readonly object Gate = new();
    public static int Sum(params int[] xs)
    {
        int s = 0;
        lock (Gate) foreach (int x in xs) s += x;
        return s;
    }
    public static string Pick(object o) => "object";
    public static string Pick(string s) => "string";
}

class Program
{
    static IEnumerable<int> Evens(int[] a)
    {
        for (int i = 0; i < a.Length; i++)
            if (a[i] % 2 == 0) yield return a[i];
    }
    static void Main()
    {
        var r = new Report { Last = { [2] = 9 } };
        Console.WriteLine($"{r.Tag.Length} {string.Join(' ', r.Last)}");
        Console.WriteLine(Fmt.Sum(1, 2, 3) + " "
            + Fmt.Pick((object)"s"));
        Console.WriteLine(string.Join(" ", Evens([1, 2, 3, 4])));
    }
}
