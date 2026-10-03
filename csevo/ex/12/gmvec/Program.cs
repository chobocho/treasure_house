// 슬라이드 p12-v11-math-vec — 제네릭 수 위에 세운 제네릭 형식, C# 11.0
using System;
using System.Numerics;

readonly struct Vec2<T> : IAdditionOperators<Vec2<T>, Vec2<T>, Vec2<T>>,
    IAdditiveIdentity<Vec2<T>, Vec2<T>>
    where T : INumber<T>
{
    public readonly T X, Y;
    public Vec2(T x, T y) { X = x; Y = y; }
    public static Vec2<T> operator +(Vec2<T> a, Vec2<T> b) =>
        new(a.X + b.X, a.Y + b.Y);
    public static Vec2<T> AdditiveIdentity => new(T.Zero, T.Zero);
    public T Dot(Vec2<T> o) => X * o.X + Y * o.Y;
    public override string ToString() => $"({X}, {Y})";
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

    static void Main()
    {
        var a = new Vec2<int>(1, 2);
        var b = new Vec2<int>(3, 4);
        Console.WriteLine(Sum(a, b, a) + " dot " + a.Dot(b));
        var c = new Vec2<double>(0.5, 1.5);
        Console.WriteLine(Sum(c, c) + " dot " + c.Dot(c));
        Console.WriteLine(Sum(new Vec2<decimal>(1.1m, 2.2m)));
    }
}
