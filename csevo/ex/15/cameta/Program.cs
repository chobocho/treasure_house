// 슬라이드 p15-v14-ca-meta — 메타데이터의 이름, C# 14
using System;
using System.Reflection;

class M
{
    public static M operator +(M a, int d) => a;
    public void operator +=(int d) { }
    public void operator checked +=(int d) { }
    public void operator ++() { }
    public void operator checked ++() { }
    public void operator >>>=(int d) { }
}

class Program
{
    static void Main()
    {
        foreach (var m in typeof(M).GetMethods(BindingFlags.Public
            | BindingFlags.Instance | BindingFlags.Static
            | BindingFlags.DeclaredOnly))
        {
            Console.WriteLine((m.IsStatic ? "static   " : "instance ")
                + m.ReturnType.Name.PadRight(5) + m.Name
                + "(" + m.GetParameters().Length + ")"
                + (m.IsSpecialName ? " specialname" : ""));
        }
    }
}
