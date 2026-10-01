// 슬라이드 p3-v2-pragma — #pragma warning, C# 2.0
using System;

class App
{
    static void Main()
    {
#pragma warning disable 168, 219
        int unused;
        int assigned = 1;
#pragma warning restore 168, 219
        Console.WriteLine("ok");
    }
}
