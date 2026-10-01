// 슬라이드 p4-v3-query-into — into 로 이어 쓰는 쿼리, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] words = { "banana", "apple", "cherry",
                           "blueberry", "avocado", "apricot" };

        IEnumerable<string> q1 =
            from w in words
            group w by w[0] into g
            where g.Count() > 1
            orderby g.Key descending
            select g.Key + "=" + g.Count();

        // 12.22.3.2: "from x2 in ( from x1 in e1 b1 ) b2"
        IEnumerable<string> q2 =
            from g in (from w in words group w by w[0])
            where g.Count() > 1
            orderby g.Key descending
            select g.Key + "=" + g.Count();

        Console.WriteLine(string.Join(" ", q1));
        Console.WriteLine(string.Join(" ", q2));
    }
}
