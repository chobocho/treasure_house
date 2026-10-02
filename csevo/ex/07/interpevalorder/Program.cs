// 슬라이드 p7-v6-interp-order — 왼쪽에서 오른쪽으로 한 번씩, C# 6.0
using System;

class App
{
    static int calls;

    static int Next()
    {
        return ++calls;
    }

    static void Main()
    {
        int i = 0;
        Console.WriteLine($"{i++} {i++} {i} {i += 10}");
        Console.WriteLine($"{Next()} {Next()} {Next()}");
        Console.WriteLine("calls = " + calls);
        string empty = $"";
        string plain = $"no holes";
        Console.WriteLine($"[{empty}] [{plain}]");
    }
}
