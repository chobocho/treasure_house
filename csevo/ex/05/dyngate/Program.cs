// 슬라이드 p5-v4-dyn-gate — dynamic, C# 4.0
using System;

class Program
{
    static void Main()
    {
        dynamic x = "a string";
        Console.WriteLine(x + 6);
        x = 4;
        Console.WriteLine(x + 6);
        x = 4.5;
        Console.WriteLine(x + 6);
    }
}
