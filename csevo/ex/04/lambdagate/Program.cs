// 슬라이드 p4-v3-lambda-gate — 람다 식, C# 3.0
using System;

class App
{
    static void Main()
    {
        Converter<int, int> twice = x => x * 2;
        Predicate<string> empty = s => s.Length == 0;
        Console.WriteLine(twice(21) + " " + empty(""));
    }
}
