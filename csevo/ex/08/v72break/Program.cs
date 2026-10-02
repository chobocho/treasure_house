// 슬라이드 p8-v7_2-small — default ?? 가 막힌 C# 7.2, C# 7.2
using System;

class App
{
    static void Main()
    {
        int x = default ?? 1;      // accepted by the C# 7.1 compiler
        Console.WriteLine(x);
    }
}
