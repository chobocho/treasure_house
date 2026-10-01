// 슬라이드 p4-v3-lambda-later — static 람다와 버림 매개변수, C# 9
using System;

class App
{
    static void Main()
    {
        Func<int, int> inc = static x => x + 1;   // may capture nothing
        Func<int, int, int> first = (a, _) => a;  // discard parameter
        Console.WriteLine(inc(1) + " " + first(7, 8));
    }
}
