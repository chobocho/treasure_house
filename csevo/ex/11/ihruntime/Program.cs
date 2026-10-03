// 슬라이드 p11-v10-ih-runtime — .NET 10 의 처리기 형식, C# 10.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static readonly Type Mark =
        typeof(InterpolatedStringHandlerAttribute);

    static bool IsHandler(Type t) =>
        (t.IsByRef ? t.GetElementType() : t).IsDefined(Mark, false);

    static void Main()
    {
        Assembly core = typeof(object).Assembly;
        Console.WriteLine(core.GetName().Name + ":");
        var types = core.GetTypes()
            .Where(t => (t.IsPublic || t.IsNestedPublic)
                        && IsHandler(t))
            .Select(t => t.FullName.Replace('+', '.'))
            .OrderBy(s => s, StringComparer.Ordinal);
        foreach (string t in types) Console.WriteLine("  " + t);

        Console.WriteLine("public methods taking one:");
        var users = core.GetExportedTypes()
            .SelectMany(t => t.GetMethods(BindingFlags.Public
                | BindingFlags.Static | BindingFlags.Instance
                | BindingFlags.DeclaredOnly))
            .Where(m => m.GetParameters()
                         .Any(p => IsHandler(p.ParameterType)))
            .GroupBy(m => m.DeclaringType.Name + "." + m.Name)
            .Select(g => g.Key + " x" + g.Count())
            .OrderBy(s => s, StringComparer.Ordinal);
        foreach (string u in users) Console.WriteLine("  " + u);
    }
}
