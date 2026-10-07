// 슬라이드 p15-v14-etargs — 식 트리 안의 선택·명명 인수, C# 14
using System;
using System.Linq.Expressions;

class Program
{
    public static string Fmt(int n, string unit = "kg", int width = 6)
        =>
        (n + unit).PadLeft(width);

    static void Show(Expression<Func<int, string>> e)
    {
        var call = (MethodCallExpression)e.Body;
        Console.WriteLine(e);
        Console.WriteLine("  args: " + call.Arguments.Count
            + "  -> [" + e.Compile()(5) + "]");
    }

    static void Main()
    {
        Show(n => Fmt(n));                      // optional arguments
        Show(n => Fmt(n, unit: "lb"));          // named, in position
#if SKIP
        Show(n => Fmt(n, width: 4));            // skips 'unit'
#endif
    }
}
