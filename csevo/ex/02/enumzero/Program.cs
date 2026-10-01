// 슬라이드 p2-v1-enumzero — 0 만 열거형으로 바로 간다, C# 1.0
using System;

enum Color { Red, Green, Blue }

class App
{
    static void Main()
    {
        Color a = 0;
        Color b = 1;
        int n = Color.Green;
        Console.WriteLine(a + " " + b + " " + n);
    }
}
