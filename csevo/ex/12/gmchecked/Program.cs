// 슬라이드 p12-v11-math-checked — 제네릭 코드 안의 checked, C# 11.0
using System;
using System.Numerics;

// Only the regular + : checked(a + b) falls back to the default body
struct W : IAdditionOperators<W, W, W>
{
    public int V;
    public static W operator +(W a, W b)
    {
        Console.Write("[W.+] ");
        return new W { V = a.V + b.V };
    }
}

class App
{
    static T Add<T>(T a, T b) where T : IAdditionOperators<T, T, T>
        => a + b;
    static T AddC<T>(T a, T b) where T : IAdditionOperators<T, T, T>
        => checked(a + b);

    static void Main()
    {
        Console.WriteLine(Add(int.MaxValue, 1));
        try { Console.WriteLine(AddC(int.MaxValue, 1)); }
        catch (OverflowException) { Console.WriteLine("Overflow"); }
        Console.WriteLine(AddC(double.MaxValue, double.MaxValue));
        Console.WriteLine(AddC(new W { V = 1 }, new W { V = 2 }).V);
    }
}
