// 슬라이드 p3-v2-lazy — 부를 때가 아니라 꺼낼 때 돈다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Numbers()
    {
        Console.WriteLine("  [start]");
        for (int i = 1; i <= 3; i++)
        {
            Console.WriteLine("  [yield " + i + "]");
            yield return i;
        }
        Console.WriteLine("  [end]");
    }

    static void Main()
    {
        IEnumerable<int> seq = Numbers();
        Console.WriteLine("Numbers() returned");
        foreach (int x in seq)
        {
            Console.WriteLine("got " + x);
        }
    }
}
