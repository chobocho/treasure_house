// 슬라이드 p15-v14-sp-bcl — 스팬 변환이 기대는 .NET 10 의 멤버, C# 14
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static string Sig(MethodInfo m) => m.ReturnType.Name + " "
        + m.DeclaringType.Name + "." + m.Name + "("
        + string.Join(", ", m.GetParameters()
            .Select(p => p.ParameterType.Name)) + ")";

    static void Show(Type t, string name, int args)
    {
        foreach (string s in t.GetMethods()
                     .Where(m => m.Name == name
                         && m.GetParameters().Length == args)
                     .Select(Sig).Order(StringComparer.Ordinal))
            Console.WriteLine("  " + s);
    }

    static void Main()
    {
        Show(typeof(Enumerable), "Reverse", 1);
        Show(typeof(ReadOnlySpan<object>), "CastUp", 1);
        Show(typeof(MemoryExtensions), "AsSpan", 1);
        Console.WriteLine("MemoryExtensions, by receiver type:");
        var ext = typeof(MemoryExtensions).GetMethods()
            .Where(m => m.IsDefined(typeof(ExtensionAttribute)))
            .GroupBy(m => m.GetParameters()[0].ParameterType.Name)
            .OrderBy(g => g.Key, StringComparer.Ordinal);
        foreach (var g in ext)
            Console.WriteLine("  " + g.Key.PadRight(18) + g.Count());
    }
}
