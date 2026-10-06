// 슬라이드 p14-v13-pm-bcl — 스팬 params 를 얻은 BCL 메서드, C# 13
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static string Name(Type t) =>
        t.IsArray ? Name(t.GetElementType()) + "[]"
        : !t.IsGenericType ? t.Name
        : t.Name[..t.Name.IndexOf('`')] + "<" + string.Join(",",
            t.GetGenericArguments().Select(Name)) + ">";

    static void Show(Type t, string method)
    {
        var lines = new SortedSet<string>(StringComparer.Ordinal);
        foreach (MethodInfo m in t.GetMethods())
        {
            ParameterInfo[] ps = m.GetParameters();
            if (m.Name != method || ps.Length == 0) continue;
            ParameterInfo p = ps[^1];
            string mark =
                p.IsDefined(typeof(ParamArrayAttribute)) ? "[]"
                : p.IsDefined(typeof(ParamCollectionAttribute)) ? "{}"
                : null;
            var types = ps.Select(q => Name(q.ParameterType));
            if (mark != null)
                lines.Add(mark + " " + t.Name + "." + method
                          + "(" + string.Join(", ", types) + ")");
        }
        foreach (string s in lines) Console.WriteLine(s);
    }

    static void Main()
    {
        Show(typeof(string), "Join");
        Show(typeof(System.IO.Path), "Combine");
        Show(typeof(System.Threading.Tasks.Task), "WhenAll");
        Show(typeof(Console), "WriteLine");
    }
}
