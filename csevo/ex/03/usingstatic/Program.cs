// 슬라이드 p3-v2-static-using — using static, C# 6
using System;
using static MathUtil;

static class MathUtil
{
    public static int Square(int x) { return x * x; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(Square(4));    // no "MathUtil." prefix
    }
}
