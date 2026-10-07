// 슬라이드 p15-v14-xm-meta — 확장 블록이 남기는 메타데이터, C# 14
using System;
using System.Linq;
using System.Reflection;

static class E
{
    extension(string s)
    {
        public int Len => s.Length;
        public string Twice() => s + s;
    }
}

class Program
{
    const BindingFlags All = BindingFlags.Public
        | BindingFlags.NonPublic
        | BindingFlags.Static | BindingFlags.Instance
        | BindingFlags.DeclaredOnly;

    static string Marks(MemberInfo m) => string.Join("",
        m.CustomAttributes.Select(a => " ["
            + a.AttributeType.Name.Replace("Attribute", "")
            + string.Join("", a.ConstructorArguments.Select(c => " "
                + c.Value)) + "]"));

    static void Dump(Type t, string indent)
    {
        Console.WriteLine(indent + "type " + t.Name + " : "
            + t.Attributes + Marks(t));
        foreach (MemberInfo m in t.GetMembers(All).OrderBy(m => m.Name))
            if (m is Type n) Dump(n, indent + "  ");
            else if (m is MethodInfo mi)
                Console.WriteLine(indent + "  " + (mi.IsStatic
                    ? "static " : "") + mi + Marks(mi));
            else Console.WriteLine(indent + "  " + m + Marks(m));
    }

    static void Main() => Dump(typeof(E), "");
}
