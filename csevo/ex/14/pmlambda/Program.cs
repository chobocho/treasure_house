// 슬라이드 p14-v13-pm-lambda — 람다와 대리자의 params 컬렉션, C# 13
using System;
using System.Collections.Generic;

delegate int Total(params IEnumerable<int> xs);

class Program
{
    static int Count(params ReadOnlySpan<int> xs) => xs.Length;

    static void Main()
    {
        var sum = (params ReadOnlySpan<int> xs) =>
        {
            int s = 0;
            foreach (int x in xs) s += x;
            return s;
        };
        var count = Count;                      // method group
        Total total = xs => xs is ICollection<int> c ? c.Count : -1;

        Console.WriteLine(sum(1, 2, 3) + " " + count(4, 5)
                          + " " + total(6, 7, 8));
        Console.WriteLine(sum.GetType().Name);
        Console.WriteLine(count.GetType() == sum.GetType());
        foreach (var a in sum.GetType().GetMethod("Invoke")
                     .GetParameters()[0].CustomAttributes)
            Console.WriteLine("  Invoke: " + a.AttributeType.Name);
    }
}
