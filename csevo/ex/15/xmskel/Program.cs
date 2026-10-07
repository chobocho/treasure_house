// 슬라이드 p15-v14-xm-skel — 뼈대 멤버의 몸체, C# 14
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

static class E
{
    extension(string s)
    {
        public string Twice() => s + s;
    }
}

class Program
{
    static void Main()
    {
        Type g = typeof(E).GetNestedTypes()[0];         // grouping type
        MethodInfo skel = g.GetMethod("Twice");
        byte[] il = skel.GetMethodBody().GetILAsByteArray();
        Console.WriteLine("IL of the skeleton: "
            + BitConverter.ToString(il));
        object box = RuntimeHelpers.GetUninitializedObject(g);
        try { skel.Invoke(box, null); }
        catch (TargetInvocationException e)
        {
            Console.WriteLine(e.InnerException.GetType().Name);
        }
        Console.WriteLine(E.Twice("ab"));          // implementation
    }
}
