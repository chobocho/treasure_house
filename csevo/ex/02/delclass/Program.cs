// 슬라이드 p2-v1-delclass — 대리자 선언이 만드는 클래스, C# 1.0
using System;
using System.Reflection;

delegate int Op(int a, int b);

class App
{
    static string Sig(MethodBase m)
    {
        string ps = "";
        foreach (ParameterInfo p in m.GetParameters())
            ps += (ps.Length > 0 ? ", " : "") + p.ParameterType.Name;
        return m.Name + "(" + ps + ")";
    }

    static void Main()
    {
        Type t = typeof(Op);
        Console.WriteLine("sealed class: " + (t.IsClass && t.IsSealed));
        Console.WriteLine("base:   " + t.BaseType.FullName);
        Console.WriteLine("base 2: " + t.BaseType.BaseType.FullName);

        BindingFlags f = BindingFlags.Instance | BindingFlags.Public
            | BindingFlags.DeclaredOnly;
        MethodInfo[] ms = t.GetMethods(f);
        string[] names = new string[ms.Length];
        for (int i = 0; i < ms.Length; i++)
            names[i] = Sig(ms[i]) + " : " + ms[i].ReturnType.Name;
        Array.Sort(names);
        foreach (string s in names) Console.WriteLine("  " + s);
        Console.WriteLine("  " + Sig(t.GetConstructors()[0]));
    }
}
