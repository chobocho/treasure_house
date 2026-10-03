// 슬라이드 p11-v10-ca-runtime — .NET 10 의 ThrowIf… 메서드, C# 10.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        var names = typeof(object).Assembly.GetExportedTypes()
            .SelectMany(t => t.GetMethods(BindingFlags.Public |
                BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Where(m => m.GetParameters().Any(p => p.IsDefined(
                typeof(CallerArgumentExpressionAttribute))))
            .Select(m => m.DeclaringType.Name + "." + m.Name)
            .Distinct().OrderBy(s => s, StringComparer.Ordinal)
            .ToArray();
        Console.WriteLine($"{names.Length} public static methods:");
        foreach (string n in names)
            Console.WriteLine("  " + n);
        var usage = typeof(AsyncMethodBuilderAttribute)
            .GetCustomAttribute<AttributeUsageAttribute>();
        Console.WriteLine("AsyncMethodBuilder: " + usage.ValidOn);
    }
}
