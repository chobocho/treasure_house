// 슬라이드 p4-v3-linq-multi — 두 번 열거하면 원본도 두 번, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static int loads;

    static IEnumerable<int> Load()
    {
        loads++;
        Console.WriteLine("  loading");
        yield return 1;
        yield return 2;
        yield return 3;
    }

    static void Main()
    {
        IEnumerable<int> q = Load().Where(x => x > 1);
        Console.WriteLine("count " + q.Count());
        Console.WriteLine("sum " + q.Sum());
        Console.WriteLine("loads " + loads);

        loads = 0;
        List<int> once = Load().Where(x => x > 1).ToList();
        Console.WriteLine("count " + once.Count);
        Console.WriteLine("sum " + once.Sum());
        Console.WriteLine("loads " + loads);
    }
}
