// 슬라이드 p3-v2-multi-enum — 두 번 돌리면 본문도 두 번, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static int runs;

    static IEnumerable<int> Load()
    {
        runs++;
        Console.WriteLine("  loading (run " + runs + ")");
        yield return 10;
        yield return 20;
    }

    static void Main()
    {
        IEnumerable<int> xs = Load();
        int sum = 0;
        foreach (int x in xs) sum += x;
        int count = 0;
        foreach (int x in xs) count++;
        Console.WriteLine(sum + " " + count + " runs=" + runs);

        List<int> once = new List<int>(xs);   // run it one more time
        Console.WriteLine(once.Count + " items, runs=" + runs);
    }
}
