// 슬라이드 p4-v3-et-equal — 모양이 같아도 같은 트리가 아니다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Expression<Func<int, bool>> a = x => x > 1;
        Expression<Func<int, bool>> b = x => x > 1;

        Console.WriteLine("text equal:  "
                          + (a.ToString() == b.ToString()));
        Console.WriteLine("Equals:      " + a.Equals(b));

        Dictionary<Expression, string> cache =
            new Dictionary<Expression, string>();
        cache[a] = "compiled a";
        Console.WriteLine("cache has b: " + cache.ContainsKey(b));
    }
}
