// 슬라이드 p9-v8-range — 범위 연산자 .., C# 8.0
using System;

class App
{
    static string Show(string[] a) => "[" + string.Join(" ", a) + "]";

    static void Main()
    {
        string[] w = { "a", "b", "c", "d", "e", "f" };
        Console.WriteLine(Show(w[1..4]));     // start in, end out
        Console.WriteLine(Show(w[^2..]));     // last two
        Console.WriteLine(Show(w[..2]));      // first two
        Console.WriteLine(Show(w[2..^2]));    // drop two at each end
        Console.WriteLine(Show(w[..]));       // everything (a copy)
        Console.WriteLine(Show(w[3..3]));     // empty, not an error
        Range r = 1..^1;
        Console.WriteLine(Show(w[r]));
    }
}
