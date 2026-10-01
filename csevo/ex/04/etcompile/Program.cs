// 슬라이드 p4-v3-et-compile — Compile 은 부를 때마다 새 대리자, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, int>> e = x => x * x;

        Func<int, int> f1 = e.Compile();
        Func<int, int> f2 = e.Compile();
        Console.WriteLine("f1(7) = " + f1(7) + ", f2(7) = " + f2(7));
        Console.WriteLine("same delegate: "
                          + object.ReferenceEquals(f1, f2));
        Console.WriteLine("f1 == f2:      " + (f1 == f2));
        Console.WriteLine("tree unchanged: " + e);
    }
}
