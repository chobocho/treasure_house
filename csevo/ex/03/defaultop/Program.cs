// 슬라이드 p3-v2-default — default 연산자, C# 2.0
using System;

class App
{
    static void Main()
    {
        Console.WriteLine(default(int));
        Console.WriteLine(default(string) == null);
        Console.WriteLine(default(bool));
        Console.WriteLine(default(DateTime).Ticks);
    }
}
