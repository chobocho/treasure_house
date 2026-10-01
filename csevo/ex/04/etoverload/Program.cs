// 슬라이드 p4-v3-et-overload — Func 와 Expression 오버로드, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void M(Func<int, int> f) { Console.WriteLine("Func"); }
    static void M(Expression<Func<int, int>> e)
    {
        Console.WriteLine("Expression");
    }

    static void Main()
    {
        M(x => x + 1);
    }
}
