// 슬라이드 p4-v3-et-queryable — IQueryable 의 쿼리는 식 트리, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        int[] xs = { 1, 2, 3, 4 };

        IEnumerable<int> e = from x in xs where x > 2 select x * 10;
        IQueryable<int> q = from x in xs.AsQueryable()
                            where x > 2
                            select x * 10;

        Console.WriteLine(string.Join(" ", e) + " | "
                          + string.Join(" ", q));
        Console.WriteLine(q.Expression);

        MethodCallExpression select =
            (MethodCallExpression)q.Expression;
        Console.WriteLine(select.Method.DeclaringType.Name + "."
                          + select.Method.Name + ", argument: "
                          + select.Arguments[1].NodeType);
    }
}
