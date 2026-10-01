// 슬라이드 p4-v3-ext-delegate — 값 형식 수신자는 안 된다, C# 3.0
using System;

static class IntExt
{
    public static bool IsEven(this int n) { return n % 2 == 0; }
}

class App
{
    static void Main()
    {
        int n = 4;
        Func<bool> even = n.IsEven;
        Console.WriteLine(even());
    }
}
