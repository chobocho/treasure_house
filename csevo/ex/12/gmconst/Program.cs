// 슬라이드 p12-v11-math-const — 제네릭 코드 안의 숫자 상수, C# 11.0
using System;
using System.Numerics;

class App
{
    // Average = Sum / count; count is an int, so it must become a T
    static T Average<T>(T[] xs) where T : INumber<T>
    {
        T s = T.Zero;
        foreach (T x in xs) s += x;
        return s / T.CreateChecked(xs.Length);
    }

    static T Half<T>(T x) where T : INumber<T>
    {
#if BAD
        return x / 2;                    // 2 is an int, not a T
#elif BAD2
        return x / (T)2;
#else
        T two = T.One + T.One;
        return x / two;
#endif
    }

    static void Main()
    {
        Console.WriteLine(Average(new[] { 1, 2, 4 }) + " "
            + Average(new[] { 1.0, 2.0, 4.0 }) + " "
            + Average(new[] { 1m, 2m, 4m }));
        Console.WriteLine(Half(7) + " " + Half(7.0) + " " + Half(7m));
    }
}
