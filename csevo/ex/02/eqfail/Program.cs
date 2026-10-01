// 슬라이드 p2-v1-eqfail — 구조체에는 == 가 없다, C# 1.0
using System;

struct PointS { public int X; }

class App
{
    static void Main()
    {
        PointS a = new PointS(), b = new PointS();
        a.X = 1;
        Console.WriteLine(a == b);
    }
}
