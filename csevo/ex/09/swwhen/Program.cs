// 슬라이드 p9-v8-switchexpr-when — when 가드와 _, C# 8.0
using System;

class App
{
    static string Sign(int x) => x switch
    {
        0 => "zero",
        int n when n > 0 => "positive",
        _ => "negative",
    };

    static void Main()
    {
        foreach (int x in new[] { -5, 0, 7 })
            Console.WriteLine("{0,2} {1}", x, Sign(x));
    }
}
