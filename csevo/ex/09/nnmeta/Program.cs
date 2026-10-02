// 슬라이드 p9-v8-notnull-meta — notnull 은 메타데이터의 어디에, C# 8.0
#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;

class Plain<T> { }
class Ref<T> where T : class { }
class NotNull<T> where T : notnull { }

class App
{
    static string Arg(IEnumerable<CustomAttributeData> cs, string n) =>
        string.Join("", cs.Where(a => a.AttributeType.Name == n)
            .Select(a => a.ConstructorArguments[0].Value));

    static void Show(Type g)
    {
        Type t = g.GetGenericArguments()[0];
        Console.WriteLine("{0,-16} {1,-24} {2,-9} {3}",
            g.Name.Split('`')[0] + "<" + t.Name + ">",
            t.GenericParameterAttributes,
            "attr(" + Arg(t.CustomAttributes, "NullableAttribute")
                + ")",
            "context(" + Arg(g.CustomAttributes,
                "NullableContextAttribute") + ")");
    }

    static void Main()
    {
        Show(typeof(Plain<>));
        Show(typeof(Ref<>));
        Show(typeof(NotNull<>));
        Show(typeof(Dictionary<,>));
        Show(typeof(HashSet<>));
    }
}
