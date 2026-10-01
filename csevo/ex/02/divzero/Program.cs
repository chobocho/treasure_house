// 슬라이드 p2-v1-divzero — 0 으로 나누기: 정수와 실수, C# 1.0
using System;

class App
{
    static void Main()
    {
        double dz = 0;
        Console.WriteLine(1.0 / dz);
        Console.WriteLine(-1.0 / dz);
        Console.WriteLine(0.0 / dz);
        Console.WriteLine(5.0 % dz);

        int iz = 0;
        Console.WriteLine(5 / iz);                      // throws
    }
}
