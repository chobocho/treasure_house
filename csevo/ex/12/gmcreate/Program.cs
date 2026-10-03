// 슬라이드 p12-v11-math-create — 값을 T 로 바꾸는 세 방법, C# 11.0
using System;
using System.Numerics;

class App
{
    static string Try<T>(Func<T> f)
    {
        try { return f().ToString(); }
        catch (OverflowException) { return "Overflow"; }
    }

    static void Row<TTo, TFrom>(TFrom v)
        where TTo : INumberBase<TTo> where TFrom : INumberBase<TFrom>
    {
        Console.WriteLine(typeof(TFrom).Name.PadRight(6) + v.ToString()
            .PadLeft(12) + " -> " + typeof(TTo).Name.PadRight(5)
            + Try(() => TTo.CreateChecked(v)).PadLeft(9)
            + TTo.CreateSaturating(v).ToString().PadLeft(11)
            + TTo.CreateTruncating(v).ToString().PadLeft(11));
    }

    static void Main()
    {
        Console.WriteLine("from         value    to     "
            + "Checked Saturating Truncating");
        Row<byte, int>(200);
        Row<byte, int>(300);
        Row<byte, int>(-5);
        Row<sbyte, int>(200);
        Row<int, double>(3.7);
        Row<int, double>(-3.7);
        Row<int, double>(1e10);
        Row<int, double>(double.NaN);
    }
}
