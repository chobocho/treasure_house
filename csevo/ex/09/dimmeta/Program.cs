// 슬라이드 p9-v8-dim-meta — 메타데이터에 남는 것, C# 8.0
using System;
using System.Reflection;

interface IDemo
{
    void Abstract();
    void Default() { }
    sealed void Sealed() { }
    private void Private() { }
    static void Static() { }
    protected void Protected() { }
}

class App
{
    static void Main()
    {
        const BindingFlags all = BindingFlags.Public
            | BindingFlags.NonPublic | BindingFlags.Instance
            | BindingFlags.Static | BindingFlags.DeclaredOnly;
        Console.WriteLine("{0,-10} {1,-9} {2,-8} {3,-7} {4}",
            "method", "access", "abstract", "virtual", "final");
        foreach (string n in new[] { "Abstract", "Default", "Sealed",
                                     "Private", "Static", "Protected" })
        {
            MethodInfo m = typeof(IDemo).GetMethod(n, all);
            string acc = m.IsPublic ? "public" : m.IsPrivate ? "private"
                : m.IsFamily ? "family" : "?";
            Console.WriteLine("{0,-10} {1,-9} {2,-8} {3,-7} {4}",
                n, acc, m.IsAbstract, m.IsVirtual, m.IsFinal);
        }
    }
}
