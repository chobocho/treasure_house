// 슬라이드 p7-v6-usingstatic — using static, C# 6.0
using System;
using static System.Math;

class Program
{
    static double Hypot(double a, double b) => Sqrt(a * a + b * b);

    static void Main()
    {
        Console.WriteLine(Hypot(3, 4));
        Console.WriteLine(Round(PI, 4));
        Console.WriteLine(Max(Abs(-7), 5));
    }
}
