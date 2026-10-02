// 슬라이드 p9-v8-nrt-bclcount — CoreLib 에 붙은 null 특성 세기, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

class App
{
    static void Main()
    {
        const BindingFlags all = BindingFlags.Public |
            BindingFlags.Instance | BindingFlags.Static |
            BindingFlags.DeclaredOnly;
        var count = new SortedDictionary<string, int>(
            StringComparer.Ordinal);
        Type[] types = typeof(object).Assembly.GetExportedTypes();
        foreach (Type t in types)
            foreach (MethodInfo m in t.GetMethods(all))
                foreach (ParameterInfo p in m.GetParameters()
                    .Append(m.ReturnParameter))
                    foreach (var a in p.CustomAttributes)
                    {
                        if (a.AttributeType.Namespace !=
                            "System.Diagnostics.CodeAnalysis") continue;
                        string n = a.AttributeType.Name;
                        if (!n.Contains("Null") &&
                            !n.Contains("Return"))
                            continue;
                        count.TryGetValue(n, out int c);
                        count[n] = c + 1;
                    }
        Console.WriteLine("public types in CoreLib: " + types.Length);
        foreach (var kv in count)
            Console.WriteLine("{0,-28} {1,5}", kv.Key, kv.Value);
    }
}
