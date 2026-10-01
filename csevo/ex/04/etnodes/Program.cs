// 슬라이드 p4-v3-et-nodes — 식 트리의 마디를 하나씩, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, bool>> e = x => x > 1;

        Console.WriteLine("whole:  " + e.NodeType + ", returns "
                          + e.ReturnType.Name);
        ParameterExpression p = e.Parameters[0];
        Console.WriteLine("param:  " + p.Name + " : " + p.Type.Name);

        BinaryExpression body = (BinaryExpression)e.Body;
        Console.WriteLine("body:   " + body.NodeType);
        Console.WriteLine("left:   " + body.Left.NodeType + " "
                          + body.Left);
        Console.WriteLine("right:  " + body.Right.NodeType + " "
                          + body.Right);
        Console.WriteLine("same x: "
                          + object.ReferenceEquals(body.Left, p));
    }
}
