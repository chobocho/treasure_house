// 슬라이드 p8-v7-throw-switch8 — switch 식의 팔에 throw 식, C# 8.0
using System;

class App
{
    static string Name(int day) => day switch
    {
        0 => "Sun",
        6 => "Sat",
        _ when day > 0 && day < 6 => "weekday",
        _ => throw new ArgumentOutOfRangeException(nameof(day)),
    };

    static void Main()
    {
        Console.WriteLine(Name(0) + " " + Name(3));
        try { Name(9); }
        catch (ArgumentOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name + " " + e.ParamName);
        }
    }
}
