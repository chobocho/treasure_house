// 슬라이드 p4-v3-et-visitor — 고치지 않고 새로 짓기, C# 3.0
using System;
using System.Linq.Expressions;

class AddToMultiply : ExpressionVisitor
{
    protected override Expression VisitBinary(BinaryExpression b)
    {
        if (b.NodeType == ExpressionType.Add)
            return Expression.Multiply(Visit(b.Left), Visit(b.Right));
        return base.VisitBinary(b);
    }
}

class Program
{
    static void Main()
    {
        Expression<Func<int, int>> e = x => x + 3;
        Expression<Func<int, int>> e2 =
            (Expression<Func<int, int>>)new AddToMultiply().Visit(e);

        Console.WriteLine(e + "  ->  " + e.Compile()(5));
        Console.WriteLine(e2 + "  ->  " + e2.Compile()(5));
    }
}
