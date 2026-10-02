// 슬라이드 p8-v7_3-runtime — 같이 온 런타임, C# 7.3
using System;
using System.Linq;
using System.Reflection;

class App
{
    static void Main()
    {
        var lib = typeof(object).Assembly;
        var pinnable = lib.GetExportedTypes()
            .Where(t => !t.IsNested)
            .Where(t => t.GetMethod("GetPinnableReference",
                        BindingFlags.Public | BindingFlags.Instance,
                        null, Type.EmptyTypes, null) != null)
            .Select(t => t.Name)
            .OrderBy(n => n, StringComparer.Ordinal);
        Console.WriteLine("GetPinnableReference: "
                          + string.Join(", ", pinnable));
        foreach (var n in new[] { "IsUnmanagedAttribute",
                                  "IsReadOnlyAttribute",
                                  "IsByRefLikeAttribute" })
        {
            var t = lib.GetType("System.Runtime.CompilerServices." + n);
            Console.WriteLine(n + ": " + (t != null && t.IsPublic));
        }
    }
}
