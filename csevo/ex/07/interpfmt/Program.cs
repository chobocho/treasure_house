// 슬라이드 p7-v6-interp-fmt — 서식 지정자와 너비, C# 6.0
using System;

class App
{
    static void Main()
    {
        double pi = Math.PI;
        int n = 255;
        DateTime day = new DateTime(2001, 2, 3, 4, 5, 6);
        decimal ratio = 0.125m;

        Console.WriteLine($"[{pi:F3}] [{pi,10:F2}] [{pi,-10:F2}]");
        Console.WriteLine($"[{n:X4}] [{n:D6}] [{n,6}] [{n,-6}]");
        Console.WriteLine($"[{day:yyyy-MM-dd HH:mm}] [{ratio:P1}]");
        Console.WriteLine($"[{"abc",5}] [{"abcdefg",5}]");

        string[] names = { "csc", "Roslyn", "dotnet" };
        int[] sizes = { 1, 323, 42 };
        for (int i = 0; i < names.Length; i++)
            Console.WriteLine($"{names[i],-8}|{sizes[i],5}|");
    }
}
