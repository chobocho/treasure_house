// 슬라이드 p14-v13-pm-expr — 식 트리와 params 컬렉션, C# 13
using System;
using System.Collections.Generic;
using System.Linq.Expressions;

class Program
{
    public static int A(params int[] xs) => xs.Length;
    public static int L(params List<int> xs) => xs.Count;

    static void Main()
    {
        Expression<Func<int>> ea = () => A(1, 2);
        Console.WriteLine(ea.Body);
#if BAD
        Expression<Func<int>> el = () => L(1, 2);
#endif
        Console.WriteLine(ea.Compile()());
    }
}
