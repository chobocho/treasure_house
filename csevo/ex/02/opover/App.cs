// 슬라이드 p2-v1-opover — 연산자 오버로딩 쓰기, C# 1.0
using System;

class App
{
    static void Main()
    {
        Money a = new Money(1250), b = new Money(375);
        Console.WriteLine(a + b);
        Console.WriteLine(a * 3);
        Console.WriteLine(-b);
        Money c = a;
        c += b;                       // += is + then assignment
        Console.WriteLine(c + " " + (c == a + b) + " " + (c != a));
        Console.WriteLine(c.Equals(a + b));
    }
}
