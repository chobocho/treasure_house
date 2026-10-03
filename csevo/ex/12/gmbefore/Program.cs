// 슬라이드 p12-v11-math-before — C# 11 이전의 우회로, C# 10.0
using System;

class App
{
    // 1) The caller passes the zero and the + as values
    static T Sum<T>(T[] xs, T zero, Func<T, T, T> add)
    {
        T s = zero;
        foreach (T x in xs) s = add(s, x);
        return s;
    }

    // 2) dynamic: + is bound at run time, on every element
    static T SumDyn<T>(T[] xs)
    {
        dynamic s = default(T);
        foreach (T x in xs) s += x;
        return (T)s;
    }

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        Console.WriteLine(Sum(a, 0, (x, y) => x + y));
        double[] d = { 0.5, 0.25 };
        Console.WriteLine(Sum(d, 0.0, (x, y) => x + y));
        Console.WriteLine(SumDyn(a) + " " + SumDyn(new[] { 1.5m }));
        try { Console.WriteLine(SumDyn(new[] { DateTime.MinValue })); }
        catch (Exception e) { Console.WriteLine(e.GetType().Name); }
    }
}
