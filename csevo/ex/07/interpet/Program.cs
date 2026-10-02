// 슬라이드 p7-v6-interp-et — 식 트리로 본 번역 결과, C# 6.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        Expression<Func<string, int, string>> e =
            (name, n) => $"{name} has {n,3:X} items";
        Console.WriteLine(e.Body);

        var call = (MethodCallExpression)e.Body;
        Console.WriteLine(call.Method.DeclaringType.Name + "." +
            call.Method.Name + "(" + call.Arguments.Count + " args)");
        Console.WriteLine(e.Compile()("Ada", 255));

        Expression<Func<int, FormattableString>> f = n => $"{n}";
        Console.WriteLine(f.Body);
    }
}
