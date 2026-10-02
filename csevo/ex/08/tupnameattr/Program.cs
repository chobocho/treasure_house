// 슬라이드 p8-v7-tuple-attr — 이름은 특성으로 남는다, C# 7.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    public static (int min, int max) Range() => (3, 9);
    public static (string name, (int x, int y) pos) Where() =>
        ("home", (1, 2));
    public static (int, string) NoNames() => (0, "");

    static void Show(string method)
    {
        MethodInfo m = typeof(App).GetMethod(method);
        ParameterInfo ret = m.ReturnParameter;
        var a = ret.GetCustomAttribute<TupleElementNamesAttribute>();
        string names = a == null ? "(none)" : string.Join(", ",
            a.TransformNames.Select(n => n ?? "null"));
        Console.WriteLine("{0,-8} {1}", method, names);
    }

    static void Main()
    {
        Show("Range");
        Show("Where");      // nested names, flattened
        Show("NoNames");
    }
}
