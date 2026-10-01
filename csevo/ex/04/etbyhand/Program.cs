// 슬라이드 p4-v3-et-byhand — Expression 팩토리로 손수 짓기, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        ParameterExpression x = Expression.Parameter(typeof(int), "x");
        Expression body = Expression.GreaterThan(
            x, Expression.Constant(1));
        Expression<Func<int, bool>> byHand =
            Expression.Lambda<Func<int, bool>>(body, x);

        Expression<Func<int, bool>> byCompiler = x2 => x2 > 1;

        Console.WriteLine(byHand);
        Console.WriteLine(byCompiler);

        Func<int, bool> f = byHand.Compile();
        Console.WriteLine(f(0) + " " + f(5));
    }
}
