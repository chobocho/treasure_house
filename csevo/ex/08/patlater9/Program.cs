// 슬라이드 p8-v7-pat-later9 — 관계·논리 패턴, C# 9.0
using System;

class App
{
    static string Grade(int score) => score switch
    {
        < 0 or > 100 => "invalid",
        >= 90 => "A",
        >= 80 and < 90 => "B",
        _ => "C",
    };

    static void Main()
    {
        foreach (int s in new[] { 95, 85, 50, 120 })
            Console.WriteLine(s + " " + Grade(s));
        object o = "x";
        if (o is not null) Console.WriteLine("not null");
    }
}
