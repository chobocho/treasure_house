// 슬라이드 p4-v3-var-rules — var 가 거절되는 다섯 자리, C# 3.0
using System;

class App
{
    static void Main()
    {
        var x;                  // no initializer
        var y = { 1, 2, 3 };    // array initializer alone
        var z = null;           // null has no type
        var u = n => n + 1;     // a lambda has no type
        var v = v++;            // refers to itself
        var a = 1, b = 2;       // two declarators
        Console.WriteLine(a + b);
    }
}
