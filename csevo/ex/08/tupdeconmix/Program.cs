// 슬라이드 p8-v7-decon-mix10 — 선언과 기존 변수를 섞기, C# 10.0
using System;

class App
{
    static void Main()
    {
        int x;
        (x, var y) = (1, 2);    // mixed: C# 10
        Console.WriteLine(x + y);
    }
}
