// 슬라이드 p5-v4-named-nontrailing — 뒤 버전: 이름 뒤 위치 인수, C# 7.2
using System;

class Program
{
    static string Resize(int width, int height, bool keepRatio)
    {
        return width + "x" + height + (keepRatio ? " (ratio)" : "");
    }

    static void Main()
    {
        Console.WriteLine(Resize(width: 640, 480, true));
        Console.WriteLine(Resize(640, height: 480, true));
#if BAD
        Console.WriteLine(Resize(height: 480, 640, true));
#endif
    }
}
