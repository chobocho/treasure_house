// 슬라이드 p7-v6-nullcond-et — 식 트리에는 못 들어간다, C# 6.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        // the C# 5 spelling of s?.Length works in a tree
        Expression<Func<string, int?>> e =
            s => s == null ? (int?)null : s.Length;
        Console.WriteLine(e.Body);
        Func<string, int?> f = s => s?.Length;  // a delegate is fine
        Console.WriteLine("[{0}] [{1}]", f("abc"), f(null));
#if BAD
        Expression<Func<string, int?>> bad = s => s?.Length;
#endif
    }
}
