// 슬라이드 p4-v3-et-cs14 — 식 트리 안의 선택적·명명된 인자, C# 14
using System;
using System.Linq.Expressions;

class Program
{
    static int Scale(int x, int factor = 10) => x * factor;

    static void Main()
    {
        Expression<Func<int, int>> a = x => Scale(x);
        Expression<Func<int, int>> b = x => Scale(x, factor: 2);
        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(a.Compile()(3) + " " + b.Compile()(3));
    }
}
