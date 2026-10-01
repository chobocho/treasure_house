// 슬라이드 p4-v3-et-walk — 식 트리를 걸으며 찍기, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Dump(Expression e, string pad)
    {
        string extra = "";
        if (e is ParameterExpression)
            extra = " " + ((ParameterExpression)e).Name;
        if (e is ConstantExpression)
            extra = " " + ((ConstantExpression)e).Value;
        Console.WriteLine(pad + e.NodeType + " : " + e.Type.Name
                          + extra);

        BinaryExpression b = e as BinaryExpression;
        if (b != null)
        {
            Dump(b.Left, pad + "  ");
            Dump(b.Right, pad + "  ");
        }
        LambdaExpression l = e as LambdaExpression;
        if (l != null)
        {
            foreach (ParameterExpression p in l.Parameters)
                Dump(p, pad + "  ");
            Dump(l.Body, pad + "  ");
        }
    }

    static void Main()
    {
        Expression<Func<int, int, bool>> e = (a, b) => a * 2 + 1 > b;
        Dump(e, "");
    }
}
