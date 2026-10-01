// 슬라이드 p4-v3-et-sql — 식 트리를 SQL 조각으로 옮기는 장난감, C# 3.0
using System;
using System.Linq.Expressions;

class Person
{
    public string Name { get; set; }
    public int Age { get; set; }
}

class Program
{
    static string Sql(Expression e)
    {
        BinaryExpression b = e as BinaryExpression;
        if (b != null)
            return "(" + Sql(b.Left) + " " + Op(b.NodeType) + " "
                   + Sql(b.Right) + ")";
        MemberExpression m = e as MemberExpression;
        if (m != null && m.Expression is ParameterExpression)
            return m.Member.Name;
        ConstantExpression c = e as ConstantExpression;
        if (c != null)
            return c.Value is string ? "'" + c.Value + "'"
                                     : c.Value.ToString();
        throw new NotSupportedException(e.NodeType.ToString());
    }

    static string Op(ExpressionType t)
    {
        switch (t)
        {
            case ExpressionType.AndAlso: return "AND";
            case ExpressionType.OrElse: return "OR";
            case ExpressionType.Equal: return "=";
            case ExpressionType.GreaterThan: return ">";
            case ExpressionType.LessThan: return "<";
        }
        throw new NotSupportedException(t.ToString());
    }

    static string Where(Expression<Func<Person, bool>> pred)
    {
        return "SELECT * FROM Person WHERE " + Sql(pred.Body);
    }

    static void Main()
    {
        Console.WriteLine(Where(p => p.Age > 30 && p.Name == "Kim"));
        Console.WriteLine(Where(p => p.Age < 20 || p.Age > 60));
        try
        {
            Console.WriteLine(Where(p => p.Name.StartsWith("K")));
        }
        catch (NotSupportedException e)
        {
            Console.WriteLine("not supported: " + e.Message);
        }
    }
}
