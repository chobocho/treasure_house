// 슬라이드 p15-v14-ca-rules — 선언의 규칙, C# 14
using System;

struct P
{
    public int X;
    public void operator +=(int d) => X += d;
    public readonly void operator -=(int d) { }    // allowed, useless
#if STATIC
    public static void operator *=(int d) { }
#endif
#if RETURN
    public P operator /=(int d) => this;
#endif
#if TWO
    public void operator %=(int a, int b) { }
#endif
#if NONPUBLIC
    void operator &=(int d) { }
#endif
#if NOTVAR
    static void Use() => new P() += 1;
#endif
}

class Program
{
    static void Main()
    {
        var p = new P();
        p += 2;
        p -= 5;
        Console.WriteLine(p.X);
    }
}
