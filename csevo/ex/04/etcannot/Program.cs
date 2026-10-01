// 슬라이드 p4-v3-et-cannot — 식 트리가 될 수 없는 람다, C# 3.0
using System;
using System.Linq.Expressions;

class Program
{
    static void Main()
    {
        Func<int, int> ok = x => { return x + 1; };     // fine as code

        Expression<Func<int, int>> a = x => { return x + 1; };
        Expression<Func<int, int>> b = x => x = 2;
        Expression<Func<int, int>> c = delegate(int x) { return x; };
        Expression<Action<string>> d = s => Console.WriteLine(s);
    }
}
