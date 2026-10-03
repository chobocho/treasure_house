// 슬라이드 p12-v11-math-user — 직접 만든 수 형식을 끼워 넣기, C# 11.0
using System;
using System.Numerics;

// Integers modulo 7: just the four interfaces the algorithms need
readonly struct Mod7 : IAdditionOperators<Mod7, Mod7, Mod7>,
    IMultiplyOperators<Mod7, Mod7, Mod7>,
    IAdditiveIdentity<Mod7, Mod7>, IMultiplicativeIdentity<Mod7, Mod7>
{
    readonly int v;
    public Mod7(int x) => v = ((x % 7) + 7) % 7;
    public static Mod7 operator +(Mod7 a, Mod7 b) => new(a.v + b.v);
    public static Mod7 operator *(Mod7 a, Mod7 b) => new(a.v * b.v);
    public static Mod7 AdditiveIdentity => new(0);
    public static Mod7 MultiplicativeIdentity => new(1);
    public override string ToString() => v + " (mod 7)";
}

class App
{
    static T Sum<T>(params T[] xs)
        where T : IAdditionOperators<T, T, T>, IAdditiveIdentity<T, T>
    {
        T s = T.AdditiveIdentity;
        foreach (T x in xs) s += x;
        return s;
    }

    static T Pow<T>(T x, int n) where T : IMultiplyOperators<T, T, T>,
        IMultiplicativeIdentity<T, T>
    {
        T r = T.MultiplicativeIdentity;
        for (int i = 0; i < n; i++) r *= x;
        return r;
    }

    static void Main()
    {
        Console.WriteLine(Sum(new Mod7(5), new Mod7(4)) + " | "
            + Sum(5, 4));
        Console.WriteLine(Pow(new Mod7(3), 6) + " | " + Pow(3, 6));
        Console.WriteLine(Pow(2.5, 2) + " | "
            + Pow(new BigInteger(2), 70));
    }
}
