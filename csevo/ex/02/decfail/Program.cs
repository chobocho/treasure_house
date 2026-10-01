// 슬라이드 p2-v1-decfail — 실수 리터럴과 decimal 사이, C# 1.0
using System;

class App
{
    static void Main()
    {
        decimal price = 0.1;
        float ratio = 1.5;
        decimal m = 2.5m;
        double d = m;
        Console.WriteLine(price + " " + ratio + " " + d);
    }
}
