// 슬라이드 p4-v3-et-runtime — 식 트리를 받쳐 주는 런타임, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Type t = typeof(Expression<Func<int, int>>);
        Console.WriteLine("assembly:  " + t.Assembly.GetName().Name);
        Console.WriteLine("base:      " + t.BaseType.Name + " <- "
                          + t.BaseType.BaseType.Name);
        Array kinds = Enum.GetValues(typeof(ExpressionType));
        Console.WriteLine("node kinds: " + kinds.Length);

        Expression<Func<int, int>> e = x => x + 1;
        Console.WriteLine("runtime type of e: " + e.GetType().Name);
    }
}
