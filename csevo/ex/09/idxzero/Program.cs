// 슬라이드 p9-v8-index-zero — ^0 은 끝 바로 뒤, C# 8.0
using System;

class App
{
    static void Try(string label, Func<int> f)
    {
        try { Console.WriteLine("{0,-10} {1}", label, f()); }
        catch (Exception e)
        {
            Console.WriteLine("{0,-10} {1}", label, e.GetType().Name);
        }
    }

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        Try("a[^1]", () => a[^1]);
        Try("a[^3]", () => a[^3]);
        Try("a[^0]", () => a[^0]);       // same as a[a.Length]
        Try("a[^4]", () => a[^4]);       // index -1
        // as the end of a range, ^0 is fine: end is exclusive
        Try("a[1..^0]", () => a[1..^0].Length);
    }
}
