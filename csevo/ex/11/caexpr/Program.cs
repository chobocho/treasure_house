// 슬라이드 p11-v10-callerarg — 인수의 식을 문자열로, C# 10.0
using System;
using System.Runtime.CompilerServices;

static class Verify
{
    public static void InRange(int arg, int low, int high,
        [CallerArgumentExpression("arg")] string argExpr = null,
        [CallerArgumentExpression("high")] string highExpr = null)
    {
        if (arg > high)
            Console.WriteLine(
                $"  {argExpr} ({arg}) > {highExpr} ({high})");
    }

    public static void ShouldBe<T>(this T self, T expected,
        [CallerArgumentExpression("self")] string selfExpr = null)
        => Console.WriteLine($"  {selfExpr}: {self} vs {expected}");
#if ODD
    public static void Odd(int x,
        [CallerArgumentExpression("nope")] string e = "default")
        => Console.WriteLine($"  [{e}]");
#endif
}

class App
{
    static void Main()
    {
        int[] a = { 1, 2, 3 };
        int index = 6;
        Verify.InRange(index, 0, a.Length - 1);
        Verify.InRange(index   *   2 /* twice */, 0, a.Length);
        a.Length.ShouldBe(3);
        Verify.ShouldBe(a[0] + a[1], 3);
        Verify.InRange(9, 0, 1, "explicit", "args");
        try
        {
            ArgumentOutOfRangeException.ThrowIfGreaterThan(index, 2);
        }
        catch (ArgumentException e) { Console.WriteLine(e.Message); }
#if ODD
        Verify.Odd(1);
#endif
    }
}
