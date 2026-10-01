// 슬라이드 p4-v3-linq-infinite — 끝없는 시퀀스와 Take·Any, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static IEnumerable<int> Naturals()
    {
        int i = 0;
        while (true) yield return i++;
    }

    static void Main()
    {
        var squares = Naturals().Where(n => n % 3 == 0)
                                .Select(n => n * n)
                                .Take(4);
        Console.WriteLine(string.Join(" ", squares));

        var small = Naturals().TakeWhile(n => n < 5);
        Console.WriteLine(string.Join(" ", small));

        bool any = Naturals().Any(n => n > 1000);
        Console.WriteLine("Any > 1000: " + any);
        // Naturals().Count() would never return
    }
}
