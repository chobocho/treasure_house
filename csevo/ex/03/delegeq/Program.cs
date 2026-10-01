// 슬라이드 p3-v2-delegate-equality — 대리자의 같음, C# 2.0
using System;

delegate void D();

class App
{
    static void M() { }

    static void Main()
    {
        D a = new D(M);
        D b = new D(M);
        Console.WriteLine("M and M:   == " + (a == b)
            + ", same object " + object.ReferenceEquals(a, b));

        D x = delegate { };
        D y = delegate { };
        Console.WriteLine("anon, anon: == " + (x == y));

        D[] ds = new D[2];
        for (int i = 0; i < 2; i++) ds[i] = delegate { };
        Console.WriteLine("one anon twice: same object "
            + object.ReferenceEquals(ds[0], ds[1]));
    }
}
