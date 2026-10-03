// 슬라이드 p12-v11-urshift — 부호 없는 오른쪽 시프트 >>>, C# 11.0
using System;

class App
{
    const int Top4 = -1 >>> 28;              // constant expression

    static void Main()
    {
        int n = -8;
        Console.WriteLine((n >> 1) + "  " + (n >>> 1));
        Console.WriteLine(Convert.ToString(n >> 1, 2).PadLeft(32));
        Console.WriteLine(
            Convert.ToString(n >>> 1, 2).PadLeft(32, '0'));
        long l = -8;
        Console.WriteLine(l >>> 1);
        nint p = -8;
        int? maybe = -8;
        Console.WriteLine((p >>> 60) + " " + (maybe >>> 1));
        n >>>= 2;
        Console.WriteLine(n + " " + Top4);
    }
}
