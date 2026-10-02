// 슬라이드 p8-v7_2-in-copy — in 과 방어 복사, C# 7.2
using System;

struct Counter
{
    public int N;
    public void Bump() { N++; }     // mutates 'this'
}

class App
{
    static readonly Counter RO = new Counter();

    static void ByIn(in Counter c)
    {
        c.Bump(); c.Bump();          // each call on a copy
        Console.WriteLine("in   c.N = " + c.N);
    }

    static void ByRef(ref Counter c)
    {
        c.Bump(); c.Bump();
        Console.WriteLine("ref  c.N = " + c.N);
    }

    static void Main()
    {
        var a = new Counter();
        ByIn(in a);
        Console.WriteLine("     a.N = " + a.N);
        var b = new Counter();
        ByRef(ref b);
        Console.WriteLine("     b.N = " + b.N);
        RO.Bump();                   // readonly field: same rule
        Console.WriteLine("    RO.N = " + RO.N);
        ref readonly Counter r = ref b;
        r.Bump();                    // ref readonly local: a copy
        Console.WriteLine("     b.N = " + b.N);
    }
}
