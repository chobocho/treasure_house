// 슬라이드 p2-v1-constswitch — case 에는 상수만, C# 1.0
using System;

class Limits
{
    public const int Max = 10;
    public static readonly int Soft = 5;
}

class App
{
    static void Main()
    {
        int n = 5;
        switch (n)
        {
            case Limits.Max: Console.WriteLine("max"); break;
            case Limits.Soft: Console.WriteLine("soft"); break;
        }
    }
}
