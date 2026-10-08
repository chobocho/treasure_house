// 슬라이드 p4-v3-query-trace-run — 쿼리마다 호출된 메서드, C# 3.0
using System;

class Program
{
    static void Main()
    {
        Q<int> s = new Q<int>(new int[] { 3, 1, 4, 1, 5 });
        object q;

        q = from x in s select x;
        Console.WriteLine("| 1");
        q = from x in s where x > 1 select x;
        Console.WriteLine("| 2");
        q = from x in s where x > 1 where x < 5 select x * 2;
        Console.WriteLine("| 3");
        q = from x in s orderby x % 2, x descending select x;
        Console.WriteLine("| 4");
        q = from x in s let y = x * x where y > 4 select y;
        Console.WriteLine("| 5");
        q = from x in s from y in new int[] { 1, 2 } select x + y;
        Console.WriteLine("| 6");
        q = from x in s group x by x % 2;
        Console.WriteLine("| 7");
        q = from x in s group x * 10 by x % 2;
        Console.WriteLine("| 8");
    }
}
