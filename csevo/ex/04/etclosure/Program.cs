// 슬라이드 p4-v3-et-closure — 잡힌 변수는 필드 접근 마디가 된다, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, bool>> c = x => x > 3;
        Console.WriteLine(c);

        int limit = 3;
        Expression<Func<int, bool>> e = x => x > limit;
        Console.WriteLine(e);

        BinaryExpression b = (BinaryExpression)e.Body;
        MemberExpression m = (MemberExpression)b.Right;
        Console.WriteLine(m.NodeType + " ." + m.Member.Name
                          + " of a " + m.Expression.NodeType);

        Func<int, bool> f = e.Compile();
        Console.WriteLine("f(4) = " + f(4));
        limit = 10;
        Console.WriteLine("f(4) = " + f(4) + " after limit = 10");
    }
}
