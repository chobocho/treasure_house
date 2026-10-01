// 슬라이드 p4-v3-query-later — 쿼리 절 안의 out 변수, C# 7.3
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] raw = { "10", "x", "7" };

        var nums = from s in raw
                   let n = int.TryParse(s, out int v) ? v : (int?)null
                   where n != null
                   select n.Value;
        Console.WriteLine(string.Join(" ", nums));
    }
}
