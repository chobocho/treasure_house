// 슬라이드 p9-v8-index — 끝에서 세는 인덱스 ^, C# 8.0
using System;

class App
{
    static void Main()
    {
        string[] days =
        {
                     // from start   from end
            "Mon",   // 0            ^7
            "Tue",   // 1            ^6
            "Wed",   // 2            ^5
            "Thu",   // 3            ^4
            "Fri",   // 4            ^3
            "Sat",   // 5            ^2
            "Sun",   // 6            ^1
        };           // 7 = Length   ^0
        Console.WriteLine(days[^1]);
        Console.WriteLine(days[^7]);
        // the C# 7.3 way: arithmetic on Length
        Console.WriteLine(days[days.Length - 2]);
        int n = 3;
        Console.WriteLine(days[^n]);
    }
}
