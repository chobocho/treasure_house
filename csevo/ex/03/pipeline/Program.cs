// 슬라이드 p3-v2-iterator-pipeline — 반복기를 잇는 파이프라인, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Source()
    {
        for (int i = 1; i <= 4; i++)
        {
            Console.WriteLine("  source " + i);
            yield return i;
        }
    }

    static IEnumerable<int> Filter(IEnumerable<int> xs,
                                   Predicate<int> p)
    {
        foreach (int x in xs)
        {
            if (p(x)) yield return x;
        }
    }

    static IEnumerable<int> Square(IEnumerable<int> src)
    {
        foreach (int x in src)
        {
            Console.WriteLine("  square " + x);
            yield return x * x;
        }
    }

    static bool IsEven(int x) { return x % 2 == 0; }

    static void Main()
    {
        Predicate<int> even = new Predicate<int>(IsEven);
        foreach (int y in Square(Filter(Source(), even)))
        {
            Console.WriteLine("got " + y);
        }
    }
}
