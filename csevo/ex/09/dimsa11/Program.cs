// 슬라이드 p9-v8-dim-later — 인터페이스의 static abstract, C# 11.0
using System;

interface IZero<T> where T : IZero<T>
{
    static abstract T Zero { get; }        // C# 11
}

struct Meters : IZero<Meters>
{
    public double V;
    public static Meters Zero => new Meters { V = 0 };
}

class App
{
    static T Sum<T>(T[] xs) where T : IZero<T> => T.Zero;

    static void Main() =>
        Console.WriteLine(Sum(new Meters[0]).V);
}
