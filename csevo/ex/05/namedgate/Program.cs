// 슬라이드 p5-v4-named-gate — 명명 인수, C# 4.0
using System;

class Program
{
    static string Resize(int width, int height, bool keepRatio)
    {
        return width + "x" + height + (keepRatio ? " (ratio)" : "");
    }

    static void Main()
    {
        Console.WriteLine(Resize(640, 480, true));
        Console.WriteLine(Resize(width: 640, height: 480,
                                 keepRatio: true));
        Console.WriteLine(Resize(keepRatio: false, height: 480,
                                 width: 640));
    }
}
