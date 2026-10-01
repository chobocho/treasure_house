// 슬라이드 p3-v2-static-why — C# 1 의 유틸리티 클래스, C# 1.0
using System;

sealed class MathUtil                // no subclasses
{
    private MathUtil() { }           // no instances

    public static int Square(int x) { return x * x; }

    public int Cube(int x)           // forgot 'static': compiles
    {
        return x * x * x;
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(MathUtil.Square(4));
        Console.WriteLine(typeof(MathUtil).GetMethod("Cube") != null);
    }
}
