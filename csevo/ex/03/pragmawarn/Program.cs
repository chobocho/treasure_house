// 슬라이드 p3-v2-pragma-why — 끌 수 없던 경고, C# 2.0
using System;

class App
{
    static void Main()
    {
        int unused;                      // CS0168
        int assigned = 1;                // CS0219
        Console.WriteLine("ok");
    }
}
