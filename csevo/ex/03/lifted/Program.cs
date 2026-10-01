// 슬라이드 p3-v2-lifted — 끌어올린 연산자, C# 2.0
using System;

class App
{
    static string S(int? v)
    {
        return v.HasValue ? v.Value.ToString() : "null";
    }

    static void Main()
    {
        int? a = 3;
        int? n = null;
        Console.WriteLine(S(a + 1));      // 4
        Console.WriteLine(S(a + n));      // null in, null out
        Console.WriteLine(S(n * 0));      // even times zero
        Console.WriteLine(S(-n));
        int? sum = 0;
        int?[] xs = new int?[] { 1, null, 2 };
        foreach (int? x in xs)
        {
            sum += x;                     // one null poisons it
        }
        Console.WriteLine(S(sum));
    }
}
