// 슬라이드 p4-v3-query-group — group by 와 IGrouping, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] words = { "banana", "apple", "cherry",
                           "blueberry", "avocado", "apricot" };

        IEnumerable<IGrouping<char, string>> groups =
            from w in words
            group w by w[0];
        foreach (IGrouping<char, string> g in groups)
        {
            Console.WriteLine(g.Key + ": " + string.Join(" ", g));
        }

        IEnumerable<IGrouping<char, int>> lengths =
            from w in words
            group w.Length by w[0];
        foreach (IGrouping<char, int> g in lengths)
        {
            Console.WriteLine(g.Key + ": " + string.Join(" ", g));
        }
    }
}
