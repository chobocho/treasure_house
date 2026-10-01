// 슬라이드 p4-v3-et-funcvar — Func 를 넘기면 빠진다, C# 3.0
using System;
using System.Linq;
using System.Linq.Expressions;

class Program
{
    static string Static<T>(T value) { return typeof(T).Name; }

    static void Main()
    {
        IQueryable<int> src = new int[] { 1, 2, 3, 4 }.AsQueryable();
        Expression<Func<int, bool>> asTree = x => x > 2;
        Func<int, bool> asFunc = x => x > 2;

        var a = src.Where(asTree);       // Queryable.Where
        var b = src.Where(asFunc);       // Enumerable.Where
        var c = src.Where(x => x > 2);   // the lambda picks Queryable

        Console.WriteLine("tree:   " + Static(a));
        Console.WriteLine("func:   " + Static(b));
        Console.WriteLine("lambda: " + Static(c));
        Console.WriteLine(string.Join(" ", b));
    }
}
