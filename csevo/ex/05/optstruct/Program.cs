// 슬라이드 p5-v4-opt-structctor — 뒤 버전: new S() 기본값, C# 10.0
using System;

struct Plain
{
    public int X;
    public Plain(int x) { X = x; }
}

struct WithCtor
{
    public int X;
    public WithCtor() { X = 42; }        // C# 10: parameterless ctor
}

class Program
{
    static void A(Plain p = new Plain()) { Console.WriteLine(p.X); }
#if BAD
    static void B(WithCtor w = new WithCtor()) { }
#endif

    static void Main()
    {
        A();
        Console.WriteLine(new WithCtor().X + " " + default(WithCtor).X);
    }
}
