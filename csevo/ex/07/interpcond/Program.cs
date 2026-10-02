// 슬라이드 p7-v6-interp-cond — 삼항 연산자는 괄호 안에, C# 6.0
using System;

class App
{
    static void Main()
    {
        int n = 1;
        Console.WriteLine($"{n} file{(n == 1 ? "" : "s")}");
        n = 3;
        Console.WriteLine($"{n} file{(n == 1 ? "" : "s")}");
        // a colon inside parentheses is not a format
        Console.WriteLine($"{(n > 2 ? n : -n):D3}");
#if BAD
        Console.WriteLine($"{n == 1 ? "" : "s"}");
#endif
    }
}
