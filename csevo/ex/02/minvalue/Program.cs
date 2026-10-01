// 슬라이드 p2-v1-minvalue — int.MinValue 에는 짝이 없다, C# 1.0
using System;

class App
{
    static void Main()
    {
        int min = int.MinValue, max = int.MaxValue;
        Console.WriteLine("-min          = " + (-min));      // wraps
        Console.WriteLine("min - 1       = " + (min - 1));
        Console.WriteLine("max + 1       = " + (max + 1));
        Console.WriteLine("Math.Abs(-5)  = " + Math.Abs(-5));
        Console.WriteLine("Math.Abs(min) = " + Math.Abs(min)); // throws
    }
}
