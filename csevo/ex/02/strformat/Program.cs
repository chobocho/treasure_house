// 슬라이드 p2-v1-strformat — 합성 서식 String.Format, C# 1.0
using System;

class App
{
    static void Main()
    {
        int x = 7, y = 35;
        string s = String.Format("{0} + {1} = {2}", x, y, x + y);
        Console.WriteLine(s);
        Console.WriteLine("[{0,5}] [{0,-5}] [{1:X4}]", x, y);
        Console.WriteLine("{0:F2} {1:N0} {2:D3}", 3.14159, 1234567, 7);
        Console.WriteLine("{1} before {0}", "a", "b");
        Console.WriteLine("{{0}} is printed as is");
        Console.WriteLine("x=" + x + ", y=" + y);   // concatenation
    }
}
