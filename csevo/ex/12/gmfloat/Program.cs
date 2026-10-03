// 슬라이드 p12-v11-math-float — 부동소수점 전용 인터페이스, C# 11.0
using System;
using System.Numerics;

class App
{
    // Sqrt comes from IRootFunctions, Pi from IFloatingPointConstants
    static T Hypot<T>(T a, T b) where T : IRootFunctions<T> =>
        T.Sqrt(a * a + b * b);

    static T CircleArea<T>(T r) where T : IFloatingPointConstants<T>,
        IMultiplyOperators<T, T, T> => T.Pi * r * r;

    static void Main()
    {
        Console.WriteLine(Hypot(3.0, 4.0) + " " + Hypot(3f, 4f)
            + " " + Hypot((Half)3, (Half)4));
        Console.WriteLine(CircleArea(1.0) + " | " + CircleArea(1f)
            + " | " + CircleArea((Half)1));
        Console.WriteLine(double.IsNaN(Hypot(-1.0, double.NaN)));
#if BAD
        Console.WriteLine(Hypot(3, 4));      // int has no Sqrt
#endif
    }
}
