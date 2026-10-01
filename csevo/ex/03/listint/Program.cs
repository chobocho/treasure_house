// 슬라이드 p3-v2-generics-gate — 제네릭 List<int>, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static int Sum(List<int> xs)
    {
        int total = 0;
        foreach (int x in xs)
        {
            total += x;                   // no cast, no unboxing
        }
        return total;
    }

    static void Main()
    {
        List<int> xs = new List<int>();
        xs.Add(1);
        xs.Add(2);
        Console.WriteLine(Sum(xs));
    }
}
