// 슬라이드 p4-v3-linq-mywhere — 반복기와 확장 메서드로 LINQ, C# 3.0
using System;
using System.Collections.Generic;
// no "using System.Linq" — the query below binds to MyLinq

static class MyLinq
{
    public static IEnumerable<T> Where<T>(this IEnumerable<T> src,
                                          Func<T, bool> p)
    {
        Console.WriteLine("  MyLinq.Where");
        foreach (T x in src)
        {
            if (p(x)) yield return x;
        }
    }

    public static IEnumerable<U> Select<T, U>(this IEnumerable<T> src,
                                              Func<T, U> f)
    {
        Console.WriteLine("  MyLinq.Select");
        foreach (T x in src) yield return f(x);
    }
}

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3, 4 };
        IEnumerable<int> q = from x in xs
                             where x % 2 == 0
                             select x * 10;
        Console.WriteLine("query built");
        foreach (int y in q) Console.WriteLine(y);
    }
}
