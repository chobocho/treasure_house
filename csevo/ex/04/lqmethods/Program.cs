// 슬라이드 p4-v3-linq-enumerable — Enumerable 을 세기, C# 3.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static void Main()
    {
        Type t = typeof(Enumerable);
        MethodInfo[] ms = t.GetMethods(BindingFlags.Public
                                       | BindingFlags.Static);
        int ext = ms.Count(m => m.IsDefined(
            typeof(ExtensionAttribute), false));
        int names = ms.Select(m => m.Name).Distinct().Count();
        Console.WriteLine(t.Assembly.GetName().Name + ": "
            + ms.Length + " methods, " + ext + " extension, "
            + names + " names");

        string[] pattern = { "Where", "Select", "SelectMany", "Join",
            "GroupJoin", "OrderBy", "OrderByDescending", "ThenBy",
            "ThenByDescending", "GroupBy", "Cast" };
        foreach (string p in pattern)
        {
            int n = ms.Count(m => m.Name == p);
            Console.WriteLine("  " + p.PadRight(18) + n + " overloads");
        }
    }
}
