// 슬라이드 p12-v11-ad-warn — 꺼져 있는 경고, C# 11
using System;

struct S
{
    public int X, Y;
    public int P { get; set; }

    public S(int x)
    {
        X += x;            // reads X before assigning it
        Y = P;             // reads P before assigning it
        Show();            // reads this: P still unassigned
    }

    public S(bool b)       // the proposal's example 4
    {
        if (b) X = 1;
        else Y = 2;
    }

    void Show() => Console.WriteLine("Show: {0} {1} {2}", X, Y, P);
}

class Program
{
    static void Main()
    {
        var s = new S(5);
        Console.WriteLine("{0} {1} {2}", s.X, s.Y, s.P);
        var t = new S(true);
        Console.WriteLine("{0} {1} {2}", t.X, t.Y, t.P);
    }
}
