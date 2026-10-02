// 슬라이드 p6-v5-caller-runtime — 같이 온 런타임: 특성 형식, C# 5.0
using System;
using System.Reflection;

class App
{
    static void Main()
    {
        // Every public Caller*Attribute in the runtime library.
        Assembly lib = typeof(object).Assembly;
        Console.WriteLine(lib.GetName().Name);
        Type[] all = lib.GetExportedTypes();
        Array.Sort(all,
            (a, b) => string.CompareOrdinal(a.Name, b.Name));
        foreach (Type t in all)
        {
            if (!t.Name.StartsWith("Caller")) continue;
            AttributeUsageAttribute u = (AttributeUsageAttribute)
                Attribute.GetCustomAttribute(t,
                    typeof(AttributeUsageAttribute));
            Console.WriteLine("  " + t.Namespace + "." + t.Name);
            Console.WriteLine("    sealed=" + t.IsSealed
                + " targets=" + u.ValidOn
                + " inherited=" + u.Inherited
                + " ctor args="
                + t.GetConstructors()[0].GetParameters().Length);
        }
    }
}
