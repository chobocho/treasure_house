// 슬라이드 p12-v11-newline-query — 구멍 안의 쿼리 식과 주석, C# 11.0
using System;
using System.Linq;

class App
{
    static void Main()
    {
        string[] words = { "raw", "u8", "span", "nameof", "list" };
        Console.WriteLine($"short: {string.Join(", ",
            from w in words
            where w.Length <= 4        // a comment inside the hole
            orderby w
            select w.ToUpperInvariant())}");
        Console.WriteLine($"count: {words.Count(/* block */ w =>
            w.Contains('a'))}");
#if TEXT
        Console.WriteLine($"one
            two");
#endif
    }
}
