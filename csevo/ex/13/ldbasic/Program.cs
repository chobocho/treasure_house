// 슬라이드 p13-v12-lambda-default — 람다 매개변수의 기본값, C# 12
using System;

class Program
{
    static void Main()
    {
        var incrementBy = (int source, int increment = 1) =>
            source + increment;
        Console.WriteLine(incrementBy(5));       // 6
        Console.WriteLine(incrementBy(5, 2));    // 7

        var greet = (string who = "world") => "hello " + who;
        Console.WriteLine(greet());
        Console.WriteLine(incrementBy.GetType().Name);
    }
}
