// 슬라이드 p12-v11-math-sum — 연산자를 요구하는 제약, C# 11.0
using System;
using System.Numerics;

class App
{
    // Ask only for what the body uses: + and the additive identity
    static T Sum<T>(T[] xs)
        where T : IAdditionOperators<T, T, T>, IAdditiveIdentity<T, T>
    {
        T s = T.AdditiveIdentity;
        foreach (T x in xs) s += x;
        return s;
    }

    static void Main()
    {
        Console.WriteLine(Sum(new[] { 1, 2, 3 }));
        Console.WriteLine(Sum(new[] { 0.5, 0.25 }));
        Console.WriteLine(Sum(new[] { 1.1m, 2.2m }));
        BigInteger big = BigInteger.Pow(10, 20);
        Console.WriteLine(Sum(new[] { big, big }));
    }
}
