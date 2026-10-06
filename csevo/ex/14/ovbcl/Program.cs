// 슬라이드 p14-v13-runtime-bcl — BCL 의 params 컬렉션을 센다, C# 13
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static void Count(Type anchor)
    {
        int arr = 0, coll = 0;
        var kinds = new SortedDictionary<string, int>();
        foreach (Type t in anchor.Assembly.GetExportedTypes())
        foreach (MethodBase m in t.GetMethods().Cast<MethodBase>()
                     .Concat(t.GetConstructors()))
        {
            if (m.DeclaringType != t) continue;
            ParameterInfo[] ps = m.GetParameters();
            if (ps.Length == 0) continue;
            ParameterInfo p = ps[^1];
            if (p.IsDefined(typeof(ParamArrayAttribute))) arr++;
            if (!p.IsDefined(typeof(ParamCollectionAttribute)))
                continue;
            coll++;
            string k = p.ParameterType.Name;
            kinds[k] = kinds.GetValueOrDefault(k) + 1;
        }
        Console.WriteLine(anchor.Assembly.GetName().Name
            + ": params T[] " + arr + ", params collection " + coll);
        foreach (var kv in kinds)
            Console.WriteLine("    " + kv.Key + " " + kv.Value);
    }

    static void Main()
    {
        Count(typeof(object));                 // System.Private.CoreLib
        Count(typeof(Console));                // System.Console
        Count(typeof(System.Collections.Immutable.ImmutableArray));
        Console.WriteLine(".NET " + Environment.Version);
    }
}
