// 슬라이드 p2-v1-constfail — const 의 규칙, C# 1.0
using System;
using System.Collections;

class Config
{
    public const ArrayList Items = null;      // only null allowed
    public const object Box = 1;              // boxing is not constant
    public static const int Max = 3;          // const is already static
}

class App
{
    static void Main()
    {
        Console.WriteLine(Config.Max);
    }
}
