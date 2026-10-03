// 슬라이드 p12-v11-math-base — INumberBase 의 static 도우미들, C# 11.0
using System;
using System.Numerics;

class App
{
    static void Show<T>(T x) where T : INumberBase<T>
    {
        Console.WriteLine(typeof(T).Name.PadRight(8)
            + x.ToString().PadLeft(7)
            + T.Abs(x).ToString().PadLeft(7)
            + T.IsNegative(x).ToString().PadLeft(7)
            + T.IsInteger(x).ToString().PadLeft(7)
            + T.Radix.ToString().PadLeft(4)
            + T.MaxMagnitude(x, T.One).ToString().PadLeft(7));
    }

    static void Main()
    {
        Console.WriteLine("type          x    Abs    Neg    Int"
            + " Rdx  MaxMag");
        Show(-7);
        Show(-2.5);
        Show(-2.5m);
        Show((Half)(-0.5));
        Show(new Complex(3, 4));
    }
}
