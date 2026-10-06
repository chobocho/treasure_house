// 슬라이드 p14-v13-ar-runtime — .NET 10 의 반제약 제네릭, C# 13.0
using System;
using System.Linq;
using System.Reflection;

class App
{
    const GenericParameterAttributes ByRefLike =
        GenericParameterAttributes.AllowByRefLike;

    static bool Allows(Type[] args) =>
        args.Any(a => (a.GenericParameterAttributes & ByRefLike) != 0);

    static void Main()
    {
        var pub = typeof(object).Assembly.GetTypes()
            .Where(t => t.IsPublic).ToList();
        var types = pub.Where(t => t.IsGenericTypeDefinition
            && Allows(t.GetGenericArguments())).ToList();
        var dels = types.Count(t => t.IsSubclassOf(typeof(Delegate)));
        Console.WriteLine($"types {types.Count}, delegates {dels}:");
        var rest = types.Where(t => !t.IsSubclassOf(typeof(Delegate)));
        foreach (var t in rest
                 .OrderBy(t => t.FullName, StringComparer.Ordinal))
            Console.WriteLine("  " + t.FullName);

        var all = BindingFlags.Public | BindingFlags.Static
            | BindingFlags.Instance | BindingFlags.DeclaredOnly;
        var ms = pub.SelectMany(t => t.GetMethods(all))
            .Where(m => m.IsGenericMethodDefinition
                && Allows(m.GetGenericArguments())).ToList();
        Console.WriteLine($"methods {ms.Count}:");
        foreach (var g in ms.GroupBy(m => m.DeclaringType.Name)
                 .OrderBy(g => g.Key, StringComparer.Ordinal))
            Console.WriteLine($"  {g.Key} {g.Count()}");
    }
}
