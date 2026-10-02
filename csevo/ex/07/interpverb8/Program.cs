// 슬라이드 p7-v6-interp-verb8 — @$ 순서도 허용, C# 8.0
using System;

class App
{
    static void Main()
    {
        string dir = "tmp";
        Console.WriteLine($@"C:\{dir}\a.txt");     // C# 6
        Console.WriteLine(@$"C:\{dir}\b.txt");     // C# 8
    }
}
