// 슬라이드 p11-v10-la-runtime — 자연 형식이 고르는 Func·Action, C# 10.0
using System;
using System.Linq;

class App
{
    static void Main()
    {
        var core = typeof(object).Assembly;
        foreach (string name in new[] { "Func", "Action" })
        {
            int[] arity = core.GetExportedTypes()
                .Where(t => t.Namespace == "System" && t.IsGenericType
                            && t.Name.StartsWith(name + "`"))
                .Select(t => t.GetGenericArguments().Length)
                .OrderBy(n => n).ToArray();
            Console.WriteLine($"{name,-7}{arity.Length} types, " +
                              $"type args {arity[0]}..{arity[^1]}");
        }
        Console.WriteLine(typeof(Action).Assembly.GetName().Name);
        // the 16-parameter Func: 16 inputs + 1 result
        Type f16 = typeof(Func<,,,,,,,,,,,,,,,,>);
        int count = f16.GetMethod("Invoke").GetParameters().Length;
        Console.WriteLine(count);
        var e = typeof(System.Linq.Expressions.Expression<>);
        Console.WriteLine(e.Assembly.GetName().Name);
    }
}
