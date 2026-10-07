// 슬라이드 p15-v14-et-default — 구조체 기본값과 특성 상수, C# 14
using System;
using System.Linq.Expressions;
using System.Threading;

class Program
{
    public static string Run(string q, CancellationToken ct = default,
        decimal price = 9.5m, DateTime? at = null) => q + " " + price;

    static void Main()
    {
        Expression<Func<string, string>> e = q => Run(q);
        Console.WriteLine(e.Body);
        foreach (var a in ((MethodCallExpression)e.Body).Arguments)
            Console.WriteLine("  " + a.NodeType + " : " + a.Type.Name);
        Console.WriteLine(e.Compile()("x"));
    }
}
