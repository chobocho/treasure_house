// 슬라이드 p15-v14-sp-mgroup — 메서드 그룹은 스팬 변환을 안 본다, C# 14
using System;
using System.Collections.Generic;

static class E
{
    public static void M<T>(this Span<T> s, T x)
        => Console.WriteLine("Span");
    public static void M<T>(this IEnumerable<T> e, T x)
        => Console.WriteLine("IEnumerable");
}

class Program
{
    static void Main()
    {
        int[] a = new int[1];
        a.M(0);                 // a call: span conversion considered
        Action<int> d = a.M;    // a method group: it is not
        d(0);
    }
}
