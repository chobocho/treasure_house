// 슬라이드 p2-v1-interp — 보간 문자열은 C# 6, C# 1.0
using System;

class App
{
    static void Main()
    {
        int x = 7, y = 35;
        Console.WriteLine(String.Format("{0} + {1} = {2}", x, y, 42));
        Console.WriteLine($"{x} + {y} = {x + y}");
    }
}
