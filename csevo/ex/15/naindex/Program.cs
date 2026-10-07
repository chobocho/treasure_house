// 슬라이드 p15-v14-na-index — ?[ ] 의 왼쪽 대입, C# 14
using System;
using System.Collections.Generic;

class Program
{
    static int[] scores = [10, 20, 30];
    static Dictionary<string, int> stock = new() { ["pen"] = 3 };

    static void Update(int[] a, Dictionary<string, int> d)
    {
        a?[0] = 99;
        a?[1] += 5;
        d?["pen"] -= 1;
        d?["ink"] = 7;               // the indexer setter adds a key
    }

    static void Main()
    {
        Update(null, null);
        Update(scores, stock);
        Console.WriteLine(string.Join(",", scores));
        Console.WriteLine(stock["pen"] + " " + stock["ink"]);
        try { scores?[5] = 1; }      // index still checked
        catch (IndexOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
