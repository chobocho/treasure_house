// 슬라이드 p13-v12-ce-runtime — 컬렉션 식이 기대는 런타임, C# 12
using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

class Program
{
    static void Main()
    {
        Assembly[] asms = [typeof(object).Assembly,
                           typeof(ImmutableArray).Assembly];
        var rows = new List<string>();
        foreach (Assembly a in asms)
            foreach (Type t in a.GetExportedTypes())
                if (t.GetCustomAttribute<CollectionBuilderAttribute>()
                    is { } cb)
                    rows.Add(t.Name.PadRight(22) + cb.BuilderType.Name
                             + "." + cb.MethodName);
        rows.Sort(StringComparer.Ordinal);
        rows.ForEach(Console.WriteLine);
        Type[] used = [typeof(CollectionBuilderAttribute),
                       typeof(InlineArrayAttribute),
                       typeof(CollectionsMarshal)];
        foreach (Type t in used)
            Console.WriteLine(t.Namespace + "." + t.Name + " @ "
                              + t.Assembly.GetName().Name);
        Console.WriteLine(typeof(CollectionsMarshal)
            .GetMethods().Count(m => m.Name == "SetCount"));
    }
}
