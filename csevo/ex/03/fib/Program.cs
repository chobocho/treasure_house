// 슬라이드 p3-v2-infinite — 끝없는 수열과 지역 변수, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<long> Fib()
    {
        long a = 0, b = 1;                // kept between MoveNext calls
        while (true)
        {
            yield return a;
            long t = a + b;
            a = b;
            b = t;
        }
    }

    static void Main()
    {
        foreach (long x in Fib())
        {
            if (x > 100) break;           // the caller decides the end
            Console.Write(x + " ");
        }
        Console.WriteLine();
    }
}
