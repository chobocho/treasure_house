// 슬라이드 p2-v1-boolfail — 정수는 조건이 될 수 없다, C# 1.0
using System;

class App
{
    static void Main()
    {
        int n = 1, flags = 6;
        if (n) Console.WriteLine("n");             // int is not bool
        if (n = 2) Console.WriteLine("assign");    // = where == meant
        if (flags & 2 == 2) Console.WriteLine("&"); // == binds tighter
        bool b = (bool)n;
        Console.WriteLine(b);
    }
}
