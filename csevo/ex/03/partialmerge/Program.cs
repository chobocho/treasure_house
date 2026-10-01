// 슬라이드 p3-v2-partial-merge — 조각을 합친 형식, C# 2.0
using System;

partial class Doc : IComparable      // no modifiers, no base here
{
    public int CompareTo(object o) { return 0; }
}

class App
{
    static void Main()
    {
        Type t = typeof(Doc);
        Console.WriteLine("public " + t.IsPublic);
        Console.WriteLine("sealed " + t.IsSealed);
        Console.WriteLine("base   " + t.BaseType.Name);
        string[] names = new string[t.GetInterfaces().Length];
        for (int i = 0; i < names.Length; i++)
            names[i] = t.GetInterfaces()[i].Name;
        Array.Sort(names, StringComparer.Ordinal);
        Console.WriteLine("ifaces " + string.Join(", ", names));
    }
}
