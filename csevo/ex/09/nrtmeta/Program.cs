// 슬라이드 p9-v8-nrt-meta — 메타데이터의 NullableAttribute, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

public class C
{
    public string? M(string a, string? b, List<string?> c,
        Dictionary<string, string?>? d) => null;
}

class App
{
    static string Arg(CustomAttributeTypedArgument v) =>
        v.Value is IEnumerable<CustomAttributeTypedArgument> xs
            ? "[" + string.Join(",", xs.Select(x => x.Value)) + "]"
            : v.Value + "";

    static string Attrs(IEnumerable<CustomAttributeData> cs) =>
        string.Join(" ", cs
            .Where(x => x.AttributeType.Name.StartsWith("Nullable"))
            .Select(x => x.AttributeType.Name.Replace("Attribute", "")
                + "(" + Arg(x.ConstructorArguments[0]) + ")"));

    static void Main()
    {
        MethodInfo m = typeof(C).GetMethod("M")!;
        Console.WriteLine("class C : " + Attrs(m.DeclaringType!
            .CustomAttributes));
        Console.WriteLine("method M: " + Attrs(m.CustomAttributes));
        Console.WriteLine("return  : "
            + Attrs(m.ReturnParameter.CustomAttributes));
        foreach (ParameterInfo p in m.GetParameters())
            Console.WriteLine("{0,-8}: {1}", p.Name,
                Attrs(p.CustomAttributes));
    }
}
