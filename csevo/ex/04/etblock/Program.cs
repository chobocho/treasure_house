// 슬라이드 p4-v3-et-block — API 로는 문장도 짓는다, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        // n => { int r = 1; while (n > 1) { r *= n; n--; } return r; }
        ParameterExpression n = Expression.Parameter(typeof(int), "n");
        ParameterExpression r = Expression.Variable(typeof(int), "r");
        LabelTarget done = Expression.Label(typeof(int), "done");

        Expression body = Expression.Block(
            new ParameterExpression[] { r },
            Expression.Assign(r, Expression.Constant(1)),
            Expression.Loop(
                Expression.IfThenElse(
                    Expression.GreaterThan(n, Expression.Constant(1)),
                    Expression.Block(
                        Expression.MultiplyAssign(r, n),
                        Expression.PostDecrementAssign(n)),
                    Expression.Break(done, r)),
                done));

        Func<int, int> fact =
            Expression.Lambda<Func<int, int>>(body, n).Compile();
        Console.WriteLine(fact(5) + " " + fact(10));
        Console.WriteLine(body.NodeType);
    }
}
