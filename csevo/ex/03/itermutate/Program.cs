// 슬라이드 p3-v2-iterator-mutate — 늦게 돌면 늦은 값을 본다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Doubled(List<int> src)
    {
        foreach (int x in src)
        {
            yield return x * 2;
        }
    }

    static void Main()
    {
        List<int> src = new List<int>();
        src.Add(1);
        IEnumerable<int> q = Doubled(src);
        src.Add(2);                       // added after the call
        foreach (int x in q) Console.Write(x + " ");
        Console.WriteLine();
        try
        {
            foreach (int x in q) src.Add(x);   // change while looping
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
