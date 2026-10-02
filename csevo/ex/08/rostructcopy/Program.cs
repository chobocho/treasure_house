// 슬라이드 p8-v7_2-rostruct-copy — 방어 복사가 없다, C# 7.2
using System;

struct Plain
{
    public readonly int V;
    public Plain(int v) { V = v; }
    public bool SeesWrite(Action write)
    {
        int before = V;
        write();                  // someone replaces the variable
        return V != before;       // did 'this' see it?
    }
}

readonly struct Frozen
{
    public readonly int V;
    public Frozen(int v) { V = v; }
    public bool SeesWrite(Action write)
    {
        int before = V;
        write();
        return V != before;
    }
}
// the static fields P and F are passed by in, then replaced
class App
{
    static Plain P = new Plain(1);
    static Frozen F = new Frozen(1);

    static void Test(in Plain p, in Frozen f)
    {
        bool a = p.SeesWrite(() => P = new Plain(2));
        bool b = f.SeesWrite(() => F = new Frozen(2));
        Console.WriteLine("in Plain : " + a);
        Console.WriteLine("in Frozen: " + b);
    }

    static void Main()
    {
        Test(in P, in F);
        bool c = P.SeesWrite(() => P = new Plain(3));
        Console.WriteLine("field P  : " + c);
    }
}
