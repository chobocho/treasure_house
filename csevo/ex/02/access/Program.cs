// 슬라이드 p2-v1-access — 다섯 가지 접근 수준, C# 1.0
using System;
using System.Reflection;

class Sample
{
    public void Pub() { }
    protected void Prot() { }
    internal void Intl() { }
    protected internal void ProtIntl() { }
    private void Priv() { }
    void Default() { }                     // members default to private
}

class App
{
    static string Kind(MethodInfo m)
    {
        if (m.IsPublic) return "public";
        if (m.IsFamily) return "family (protected)";
        if (m.IsAssembly) return "assembly (internal)";
        if (m.IsFamilyOrAssembly) return "family or assembly";
        return "private";
    }

    static void Main()
    {
        BindingFlags all = BindingFlags.Instance | BindingFlags.Public
            | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
        MethodInfo[] ms = typeof(Sample).GetMethods(all);
        string[] lines = new string[ms.Length];
        for (int i = 0; i < ms.Length; i++)
            lines[i] = ms[i].Name.PadRight(9) + " " + Kind(ms[i]);
        Array.Sort(lines);
        foreach (string s in lines) Console.WriteLine(s);
        Console.WriteLine("class Sample: NotPublic = "
            + typeof(Sample).IsNotPublic);
    }
}
