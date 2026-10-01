// 슬라이드 p4-v3-ext-static — [Extension] 을 손으로 붙이면, C# 3.0
using System;
using System.Runtime.CompilerServices;

static class IntExt
{
    [Extension]
    public static bool IsOdd(int n) { return n % 2 == 1; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(IntExt.IsOdd(3));
    }
}
