// 슬라이드 p9-v8-nrt-bcl — .NET 10 의 BCL 주석 읽기, C# 8.0
#nullable enable
using System;
using System.Linq;
using System.Reflection;

class App
{
    static void Show(MethodInfo m)
    {
        foreach (ParameterInfo p in m.GetParameters())
            foreach (CustomAttributeData a in p.CustomAttributes
                .Where(x => x.AttributeType.Namespace ==
                    "System.Diagnostics.CodeAnalysis"))
                Console.WriteLine("{0}({1}): [{2}{3}]", m.Name, p.Name,
                    a.AttributeType.Name.Replace("Attribute", ""),
                    a.ConstructorArguments.Count == 0 ? ""
                        : "(" + a.ConstructorArguments[0].Value + ")");
    }

    static void Main()
    {
        Show(typeof(string).GetMethod("IsNullOrEmpty")!);
        Show(typeof(string).GetMethod("IsNullOrWhiteSpace")!);
        Show(typeof(ArgumentNullException).GetMethod("ThrowIfNull",
            new[] { typeof(object), typeof(string) })!);

        string? s = Environment.GetEnvironmentVariable("HOME");
        if (!string.IsNullOrEmpty(s))
            Console.WriteLine(s.Length > 0);   // no warning
    }
}
