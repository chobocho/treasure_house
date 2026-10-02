// 슬라이드 p8-v7_1-tuplenames-decon — 분해 대입의 이름, C# 7.1
using System;

class P
{
    public int X, Y;
}

class App
{
    static void Main()
    {
        var p = new P { Y = 5 };
        int a;
        var t = ((a, p.X) = (1, 2));     // names: a, X
        Console.WriteLine(t.a + " " + t.X + " " + p.X);
        var u = (p.X, p?.Y);             // names: X, Y
        Console.WriteLine(u.X + " " + u.Y);
    }
}
