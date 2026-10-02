// 슬라이드 p5-v4-opt-attr — 특성으로 적은 선택적 매개변수, C# 4.0
using System;
using System.Runtime.InteropServices;

class Program
{
    static void Old([Optional, DefaultParameterValue(7)] int x)
    {
        Console.WriteLine("Old(" + x + ")");
    }

    static void Bare([Optional] int y, [Optional] string s)
    {
        Console.WriteLine("Bare(" + y + ", " + (s == null) + ")");
    }

    static void Main()
    {
        Old();
        Old(1);
        Bare();
    }
}
