// 슬라이드 p8-v7-runtime — 같이 온 런타임 System.ValueTuple, C# 7.0
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        var t = (1, "a");
        Type vt = t.GetType();
        Console.WriteLine(vt.FullName.Split('[')[0]);
        Console.WriteLine("struct=" + vt.IsValueType
            + " in " + vt.Assembly.GetName().Name);
        // the family: ValueTuple, ValueTuple`1 ... ValueTuple`8
        var family = typeof(ValueTuple).Assembly.GetExportedTypes()
            .Where(x => x.Namespace == "System"
                && x.Name.StartsWith("ValueTuple"))
            .Select(x => x.Name).OrderBy(n => n.Length).ThenBy(n => n);
        Console.WriteLine(string.Join(" ", family));
        // what a ValueTuple`2 implements
        var ifs = vt.GetInterfaces().Select(i => i.Name)
            .OrderBy(n => n);
        Console.WriteLine(string.Join(" ", ifs));
        // the attribute that carries element names
        Type a = typeof(TupleElementNamesAttribute);
        Console.WriteLine(a.FullName + " in "
            + a.Assembly.GetName().Name);
        // the old package name survives as a type-forwarding facade
        var facade = Assembly.Load("System.ValueTuple");
        Console.WriteLine(facade.GetName().Name + ": forwards "
            + facade.GetForwardedTypes().Length + " types, defines "
            + facade.GetTypes().Length);
        var other = facade.GetForwardedTypes().Select(x => x.Name)
            .Where(n => !n.StartsWith("ValueTuple")).OrderBy(n => n);
        Console.WriteLine("  + " + string.Join(" ", other));
    }
}
