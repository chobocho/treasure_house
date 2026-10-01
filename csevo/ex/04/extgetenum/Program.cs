// 슬라이드 p4-v3-ext-getenum — foreach 와 확장 GetEnumerator, C# 9
using System;
using System.Collections.Generic;

static class RangeExt
{
    public static IEnumerator<int> GetEnumerator(this int count)
    {
        for (int i = 0; i < count; i++) yield return i;
    }
}

class App
{
    static void Main()
    {
        foreach (int i in 3)        // int has no GetEnumerator
            Console.Write(i + " ");
        Console.WriteLine();
    }
}
