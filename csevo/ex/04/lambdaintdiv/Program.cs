// 슬라이드 p4-v3-lambda-intdiv — 본문은 매개변수 형식으로, C# 3.0
using System;

class App
{
    static void Main()
    {
        Func<int, double> half = x => x / 2;   // int / int, then double
        Func<int, double> half2 = x => x / 2.0;
        Console.WriteLine(half(3) + " " + half2(3));
    }
}
