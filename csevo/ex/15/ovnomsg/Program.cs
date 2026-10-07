// 슬라이드 p15-v14-gates-quiet — 기능 이름 없이 거절되는 둘, C# 14
using System;
using System.Linq.Expressions;

static class E
{
    public static int N(this ReadOnlySpan<int> s) => s.Length;
}

class Program
{
    static int Add(int a, int b = 10) => a + b;

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        Console.WriteLine(a.N());                   // first-class span
        Expression<Func<int, int>> e = x => Add(x); // optional argument
        Console.WriteLine(e + " = " + e.Compile()(1));
    }
}
