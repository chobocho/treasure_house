// 슬라이드 p11-v10-wi-order — with 의 순서, C# 10.0
using System;

struct Pt
{
    int x, y;
    public int X
    {
        get => x;
        set { Console.WriteLine("set X"); x = value; }
    }
    public int Y
    {
        get => y;
        set { Console.WriteLine("set Y"); y = value; }
    }
}

class App
{
    static int Log(string s, int v)
    {
        Console.WriteLine("eval " + s);
        return v;
    }

    static void Main()
    {
        var a = new Pt();
        var b = a with { Y = Log("y", 2), X = Log("x", 1) };
        Console.WriteLine(b.X + "," + b.Y + " / " + a.X + "," + a.Y);
    }
}
