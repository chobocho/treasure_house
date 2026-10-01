// 슬라이드 p4-v3-ext-enum — enum 에 메서드를 붙이기, C# 3.0
using System;

enum Light { Red, Green, Yellow }

static class LightExt
{
    public static Light Next(this Light l)
    {
        switch (l)
        {
            case Light.Red: return Light.Green;
            case Light.Green: return Light.Yellow;
            default: return Light.Red;
        }
    }
}

class App
{
    static void Main()
    {
        Light l = Light.Red;
        for (int i = 0; i < 4; i++)
        {
            Console.Write(l + " ");
            l = l.Next();
        }
        Console.WriteLine();
    }
}
