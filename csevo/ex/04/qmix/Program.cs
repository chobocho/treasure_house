// 슬라이드 p4-v3-query-mix — 키워드가 없는 연산자는 메서드로, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        int[] xs = { 5, 3, 8, 3, 9, 1 };

        int n = (from x in xs where x > 2 select x).Count();
        int[] top = (from x in xs orderby x descending select x)
                    .Distinct().Take(3).ToArray();
        int first = (from x in xs where x % 2 == 0 select x).First();

        Console.WriteLine(n + " | " + string.Join(" ", top)
                          + " | " + first);
    }
}
