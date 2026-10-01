// 슬라이드 p4-v3-var-literal — var 는 식의 형식을 받는다, C# 3.0
using System;

class App
{
    static void Main()
    {
        var a = 3000000000;      // too big for int
        var b = 1.5;
        var c = 1.5f;
        var d = 1.5m;
        var e = 'x';
        byte one = 1;
        var f = one + one;       // byte + byte
        var g = 7 / 2;           // int / int
        Console.WriteLine(a.GetType() + " " + b.GetType());
        Console.WriteLine(c.GetType() + " " + d.GetType());
        Console.WriteLine(e.GetType() + " " + f.GetType());
        Console.WriteLine(g.GetType() + " = " + g);
    }
}
