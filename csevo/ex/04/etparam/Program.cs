// 슬라이드 p4-v3-et-param — 이름이 같아도 다른 매개변수, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, bool>> a = x => x > 1;
        Expression<Func<int, bool>> b = x => x < 5;

        var both = Expression.Lambda<Func<int, bool>>(
            Expression.AndAlso(a.Body, b.Body), a.Parameters);
        Console.WriteLine(both);
        try
        {
            both.Compile();
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }

        var fixd = Expression.Lambda<Func<int, bool>>(
            Expression.AndAlso(a.Body,
                Expression.Invoke(b, a.Parameters[0])), a.Parameters);
        Console.WriteLine(fixd);
        Func<int, bool> f = fixd.Compile();
        Console.WriteLine(f(3) + " " + f(7));
    }
}
