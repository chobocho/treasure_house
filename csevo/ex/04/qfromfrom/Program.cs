// 슬라이드 p4-v3-query-selectmany — from 두 개는 SelectMany, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] suits = { "S", "H" };
        string[] ranks = { "A", "K", "Q" };

        IEnumerable<string> q1 = from s in suits
                                 from r in ranks
                                 select r + s;
        IEnumerable<string> q2 = suits.SelectMany(s => ranks,
                                                  (s, r) => r + s);
        Console.WriteLine(string.Join(" ", q1));
        Console.WriteLine(string.Join(" ", q2));

        // the second source may depend on the first range variable
        string[] words = { "ab", "cde" };
        IEnumerable<char> letters = from w in words
                                    from c in w
                                    select c;
        Console.WriteLine(string.Join(",", letters));
    }
}
