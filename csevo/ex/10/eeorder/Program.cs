// 슬라이드 p10-v9-ee-order — 확장은 마지막 후보, C# 9.0
using System;
using System.Collections;
using System.Collections.Generic;

class Bag : IEnumerable<int>
{
    public IEnumerator<int> GetEnumerator()
    {
        yield return 1; yield return 2;
    }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

static class Ext
{
    public static IEnumerator<int> GetEnumerator(this Bag b)
    {
        yield return 99;                    // never chosen
    }
    public static IEnumerator<int> GetEnumerator(this int n)
    {
        for (int i = 0; i < n; i++) yield return i;
    }
}

class App
{
    static void Main()
    {
        foreach (int x in new Bag()) Console.Write(x + " ");
        Console.WriteLine();
        foreach (int x in 3) Console.Write(x + " ");     // an int!
        Console.WriteLine();
    }
}
