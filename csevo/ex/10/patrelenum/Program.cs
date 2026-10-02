// 슬라이드 p10-v9-pat-relenum — 되는 형식과 안 되는 형식, C# 9.0
using System;

enum Level { Low = 1, Mid = 5, High = 9 }

class App
{
    static string Of(Level l) => l switch
    {
        < Level.Low => "below",
        < Level.Mid => "low",
        < Level.High => "mid",
        _ => "high",
    };

    static void Main()
    {
        Level[] all = { (Level)0, Level.Low, (Level)7, Level.High };
        foreach (Level l in all)
            Console.Write(Of(l) + " ");
        nint n = 5;
        Console.WriteLine(n is > 3 and < 10);
#if BAD
        string s = "b";
        Console.WriteLine(s is > "a");
#endif
    }
}
