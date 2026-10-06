// 슬라이드 p13-v12-rr-meta — ref readonly 의 메타데이터, C# 12.0
using System;
using System.Linq;
using System.Reflection;

delegate int D(ref readonly int x);

abstract class Shape
{
    public abstract int Virt(ref readonly int x);
    public static int Stat(ref readonly int x) => x;
    public static int StatIn(in int x) => x;
}

class App
{
    static void Show(string label, ParameterInfo p)
    {
        var attrs = p.GetCustomAttributes(false)
                     .Select(a => a.GetType().Name);
        var mods = p.GetRequiredCustomModifiers().Select(t => t.Name);
        Console.WriteLine(label + ": " + p.ParameterType.Name
            + " attrs=[" + string.Join(",", attrs) + "]"
            + " modreq=[" + string.Join(",", mods) + "]");
    }

    static ParameterInfo P(Type t, string m) =>
        t.GetMethod(m).GetParameters()[0];

    static void Main()
    {
        Show("abstract rr", P(typeof(Shape), "Virt"));
        Show("static rr  ", P(typeof(Shape), "Stat"));
        Show("delegate rr", P(typeof(D), "Invoke"));
        Show("static in  ", P(typeof(Shape), "StatIn"));
    }
}
