// 슬라이드 p10-v9-nint-later11 — nint 와 제네릭 수학, C# 11.0
using System;
using System.Numerics;

class App
{
    static T Sum<T>(T[] xs) where T : INumber<T>
    {
        T s = T.Zero;
        foreach (T x in xs) s += x;
        return s;
    }

    static void Main()
    {
        nint[] a = { 1, 2, 3 };
        Console.WriteLine(Sum(a) + " " + Sum(new[] { 1.5, 2.5 }));
        Type num = typeof(INumber<nint>);
        Console.WriteLine(num.IsAssignableFrom(typeof(nint)));
    }
}
