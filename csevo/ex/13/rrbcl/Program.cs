// 슬라이드 p13-v12-rr-runtime — .NET 10 의 ref readonly, C# 12.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;

class App
{
    const BindingFlags All = BindingFlags.Public | BindingFlags.Static
        | BindingFlags.Instance | BindingFlags.DeclaredOnly;

    static bool IsRR(ParameterInfo p) => p.GetCustomAttributes(false)
        .Any(a => a.GetType().Name == "RequiresLocationAttribute");

    static void Main()
    {
        var core = typeof(object).Assembly;
        var hits = new List<string>();
        int n = 0;
        foreach (var t in core.GetExportedTypes())
            foreach (var m in t.GetMethods(All).Cast<MethodBase>()
                               .Concat(t.GetConstructors()))
                foreach (var p in m.GetParameters().Where(IsRR))
                {
                    n++;
                    hits.Add(t.Name + "." + m.Name);
                }
        Console.WriteLine(core.GetName().Name + ": " + n
                          + " parameters");
        var cmp = StringComparer.Ordinal;
        foreach (var s in hits.Distinct().OrderBy(s => s, cmp))
            Console.WriteLine("  " + s);
        var iid = typeof(Marshal).GetMethod("QueryInterface")
                                 .GetParameters()[1];
        Console.WriteLine("QueryInterface(" + iid.Name + "): rr="
            + IsRR(iid) + " in=" + iid.IsIn);
    }
}
