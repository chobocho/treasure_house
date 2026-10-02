// 슬라이드 p9-v8-pat-rel9 — 관계·논리 패턴, C# 9
using System;

class App
{
    // C# 8.0 needed: int n when n < 0 => ...
    static string Grade(int score) => score switch
    {
        < 0 or > 100 => "invalid",
        >= 90 => "A",
        >= 80 and < 90 => "B",
        not 0 => "C or below",
        _ => "zero",
    };

    static void Main()
    {
        foreach (int s in new[] { -1, 95, 85, 50, 0 })
            Console.WriteLine("{0,3} {1}", s, Grade(s));
    }
}
