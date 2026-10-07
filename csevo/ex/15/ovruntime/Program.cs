// 슬라이드 p15-v14-runtime — C# 14 기능이 기대는 형식, C# 14
using System;
using System.Linq;

class Program
{
    static void Show(string name)
    {
        Type t = Type.GetType(name);
        Console.WriteLine(name.Substring(name.LastIndexOf('.') + 1)
            .PadRight(34) + (t == null ? "none"
            : t.Assembly.GetName().Name));
    }

    static void Has(Type t, string method, string param)
    {
        bool found = t.GetMethods().Any(m => m.Name == method
            && m.GetParameters()[0].ParameterType.Name == param);
        Console.WriteLine((t.Name + "." + method + "(" + param + ")")
            .PadRight(34) + found);
    }

    static void Main()
    {
        const string NS = "System.Runtime.CompilerServices.";
        Show(NS + "ExtensionAttribute");              // 2장
        Show(NS + "ExtensionMarkerAttribute");        // 2장
        Show(NS + "ExtensionMarkerNameAttribute");    // the proposal's
        Has(typeof(Enumerable), "Reverse", "TSource[]"); // 4장
        Has(typeof(Enumerable), "Reverse", "IEnumerable`1");
        Has(typeof(MemoryExtensions), "Reverse", "Span`1");
        Console.WriteLine(Environment.Version);
    }
}
