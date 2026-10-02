// 슬라이드 p9-v8-range-err — 범위가 어긋나면, C# 8.0
using System;

class App
{
    static void Try(string label, Func<int> f)
    {
        try { Console.WriteLine("{0,-12} {1}", label, f()); }
        catch (Exception e)
        {
            Console.WriteLine("{0,-12} {1}", label, e.GetType().Name);
        }
    }

    static void Main()
    {
        int[] a = { 1, 2, 3, 4 };
        string s = "abcd";
        Try("a[1..1]", () => a[1..1].Length);
        Try("a[3..1]", () => a[3..1].Length);      // start > end
        Try("a[2..9]", () => a[2..9].Length);      // past the end
        Try("s[3..1]", () => s[3..1].Length);
        Try("a[^9..]", () => a[^9..].Length);      // before 0
        Try("span[3..1]", () => a.AsSpan()[3..1].Length);
    }
}
