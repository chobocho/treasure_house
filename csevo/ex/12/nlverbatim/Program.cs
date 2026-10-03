// 슬라이드 p12-v11-newline-verbatim — 이전엔 $@ 로 썼다, C# 11.0
using System;

class App
{
    static void Main()
    {
        int[] xs = { 4, 8, 15 };
        Console.WriteLine($@"sum: {xs[0]
            + xs[1]
            + xs[2]}");
    }
}
