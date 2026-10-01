// 슬라이드 p4-v3-var-static — var 는 정적 형식, C# 3.0
using System;

class App
{
    static void Main()
    {
        var x = 1;            // x is int, decided here, forever
        x = 2;                // fine
        x = 1.5;              // double → int?
        x = "one";            // string → int?
        Console.WriteLine(x);
    }
}
