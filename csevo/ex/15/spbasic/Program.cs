// 슬라이드 p15-v14-span — 암시적 Span 변환, C# 14
using System;

static class E
{
    public static int Total(this ReadOnlySpan<int> s)
    {
        int t = 0;
        foreach (int x in s) t += x;
        return t;
    }
}

class Program
{
    static int Sum(ReadOnlySpan<int> s) => s.Total();

    static void Main()
    {
        int[] arr = [1, 2, 3, 4];
        Span<int> span = arr.AsSpan(1);
        Console.WriteLine(Sum(arr) + " " + Sum(span)); // arguments
        Console.WriteLine(arr.Total());               // int[] receiver
        Console.WriteLine(span.Total());              // Span receiver
    }
}
