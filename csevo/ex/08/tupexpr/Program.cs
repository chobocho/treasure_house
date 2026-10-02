// 슬라이드 p8-v7-tuple-expr — 식 트리 안의 C# 7.0 기능, C# 7.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        Expression<Func<int, (int, int)>> a = x => (x, x);
        Expression<Func<object, bool>> b = o => o is int n;
        Expression<Func<string, bool>> c =
            s => int.TryParse(s, out int v);
        Expression<Func<int, int>> d = x => x;      // fine
        Console.WriteLine(d);
    }
}
