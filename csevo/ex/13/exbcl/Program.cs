// 슬라이드 p13-v12-ex-runtime — .NET 10 의 [Experimental] API, C# 12.0
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;

class App
{
    const BindingFlags All = BindingFlags.Public | BindingFlags.Static
        | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    const string Name = "ExperimentalAttribute";

    static void Main()
    {
        var core = typeof(object).Assembly.Location;
        var ids = new SortedDictionary<string, SortedSet<string>>(
            StringComparer.Ordinal);
        int n = 0;
        foreach (var f in Directory.GetFiles(
                     Path.GetDirectoryName(core), "*.dll"))
        {
            Type[] ts;
            try { ts = Assembly.LoadFrom(f).GetExportedTypes(); }
            catch (Exception) { continue; }    // native or broken
            foreach (var t in ts)
                foreach (var m in t.GetMembers(All).Append(t))
                    foreach (var a in m.CustomAttributes.Where(
                                 a => a.AttributeType.Name == Name))
                    {
                        n++;
                        var id = a.ConstructorArguments[0].Value
                                  .ToString();
                        if (!ids.TryAdd(id, new() { t.Name }))
                            ids[id].Add(t.Name);
                    }
        }
        Console.WriteLine(n + " members and types");
        foreach (var kv in ids)
        {
            Console.WriteLine(kv.Key + ":");
            foreach (var t in kv.Value) Console.WriteLine("  " + t);
        }
    }
}
