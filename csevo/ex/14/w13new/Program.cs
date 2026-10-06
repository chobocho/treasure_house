// 슬라이드 p14-sum-new — 같은 프로그램의 C# 13 판, C# 13
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;

partial class Report
{
    public partial string Tag { get; }             // partial property
    public partial string Tag => "\e[1mC#\e[0m";   // \e
    public int[] Last { get; } = new int[3];
}

static class Fmt
{
    static readonly Lock Gate = new();               // Lock object
    public static int Sum(params ReadOnlySpan<int> xs)  // params span
    {
        int s = 0;
        lock (Gate) foreach (int x in xs) s += x;
        return s;
    }
    [OverloadResolutionPriority(1)]                  // priority
    public static string Pick(object o) => "object";
    public static string Pick(string s) => "string";
}

class Program
{
    static IEnumerable<int> Evens(int[] a)
    {
        for (int i = 0; i < a.Length; i++)
        {
            ref int x = ref a[i];                    // ref in iterator
            if (x % 2 == 0) yield return x;
        }
    }
    static void Main()
    {
        var r = new Report { Last = { [^1] = 9 } };  // ^ in initializer
        Console.WriteLine($"{r.Tag.Length} {string.Join(' ', r.Last)}");
        Console.WriteLine(Fmt.Sum(1, 2, 3) + " " + Fmt.Pick("s"));
        Console.WriteLine(string.Join(" ", Evens([1, 2, 3, 4])));
    }
}
