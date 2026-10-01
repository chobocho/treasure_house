// 슬라이드 p3-v2-static-gate — static 클래스, C# 2.0
using System;

static class MathUtil
{
    public const int Answer = 42;    // constants are static
    public static int Square(int x) { return x * x; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(MathUtil.Square(4) + " " + MathUtil.Answer);
    }
}
