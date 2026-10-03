// 슬라이드 p11-v10-recstruct — record struct 선언, C# 10.0
using System;

record struct Point(int X, int Y);

class App
{
    static void Main()
    {
        Point a = new Point(1, 2);
        Point b = a;                         // a copy, not a reference
        b.X = 9;
        Console.WriteLine(a + " " + b);
        Console.WriteLine(a == new Point(1, 2));
    }
}
