// 슬라이드 p10-v9-extenum — 확장 GetEnumerator, C# 9.0
using System;
using System.Collections.Generic;

static class RangeExt
{
    // Range is not a collection; this makes it one for foreach.
    public static IEnumerator<int> GetEnumerator(this Range r)
    {
        for (int i = r.Start.Value; i < r.End.Value; i++)
            yield return i;
    }
}

class App
{
    static void Main()
    {
        foreach (int i in 1..4)
            Console.Write(i + " ");
        Console.WriteLine();
    }
}
