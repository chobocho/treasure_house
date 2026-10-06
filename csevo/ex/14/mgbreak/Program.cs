// 슬라이드 p14-v13-mg-break — 메서드 그룹의 깨지는 변경, C# 13
using System;

class Program
{
    static void Main()
    {
#if BAD
        var x1 = new Program().Test1; // previously Action<long[]>
        x1(new long[2]);
#endif
        var d = new C().M;  // C# 12: CS8917 / C# 13: one candidate
        d(new int[3]);
        Console.WriteLine(" " + d.GetType().Name);
    }
}

static class E
{
    static public void Test1(this Program p, long[] a)
        => Console.Write(a.Length);
    static public void Test1(this object p, params long[] a)
        => Console.Write(a.Length);

    public static void M(this C c, params int[] x)
        => Console.Write("E.M " + x.Length);
}

class C
{
    public void M(int[] x) => Console.Write("C.M " + x.Length);
}
