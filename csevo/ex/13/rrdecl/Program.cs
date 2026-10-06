// 슬라이드 p13-v12-rr-decl — ref readonly 를 둘 수 있는 곳, C# 12.0
using System;
using System.Runtime.CompilerServices;

struct Vec
{
    public int X;
    public int this[ref readonly int i] => X + i;   // indexer: ok
#if BAD
    public static Vec operator +(ref readonly Vec a, Vec b) => a;
#endif
}

static class Ext
{
    // receiver needs no 'in' at the call site
    public static int Get(this ref readonly Vec v) => v.X;
}

class App
{
#if W1
    static int D(ref readonly int r = 7) => r;  // default value
#elif BAD2
    static int A([RequiresLocation] ref int r) => r;
#elif BAD3
    static void W(ref readonly int r) { r = 1; }
#endif
    static void Main()
    {
        var v = new Vec { X = 1 };
        int k = 2;
        Console.WriteLine(v[in k] + " " + v.Get());
    }
}
