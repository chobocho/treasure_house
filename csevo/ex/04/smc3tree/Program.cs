// 슬라이드 p4-v3-wrap-tree — 같은 쿼리를 IQueryable 로, C# 3.0
using System;
using System.Linq;
using System.Linq.Expressions;

class Person
{
    public string City { get; set; }
    public int Age { get; set; }
}

class Program
{
    static void Main()
    {
        var people = new[] {
            new Person { City = "Seoul", Age = 34 },
            new Person { City = "Busan", Age = 17 },
            new Person { City = "Seoul", Age = 41 },
        }.AsQueryable();

        var counts = from p in people
                     where p.Age >= 18
                     group p by p.City into g
                     orderby g.Count() descending, g.Key
                     select new { City = g.Key, Count = g.Count() };

        // walk the chain of calls from the outermost one inwards
        Expression e = counts.Expression;
        while (e is MethodCallExpression)
        {
            MethodCallExpression call = (MethodCallExpression)e;
            Console.WriteLine(call.Method.DeclaringType.Name + "."
                + call.Method.Name + "  " + call.Arguments[1].NodeType);
            e = call.Arguments[0];
        }
        Console.WriteLine(e.NodeType + " " + e.Type.Name);
        Console.WriteLine(string.Join(", ", counts));
    }
}
