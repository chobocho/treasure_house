// 슬라이드 p9-v8-ro-bcl — .NET 10 의 Vector2 와 readonly 멤버, C# 8.0
using System;
using System.Linq;
using System.Numerics;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        Type t = typeof(Vector2);
        Console.WriteLine("readonly struct: "
            + t.IsDefined(typeof(IsReadOnlyAttribute), false));
        Console.WriteLine("mutable fields : " + string.Join(", ",
            t.GetFields().Where(f => !f.IsStatic && !f.IsInitOnly)
             .Select(f => f.Name)));

        var methods = t.GetMethods(BindingFlags.Public
                | BindingFlags.Instance | BindingFlags.DeclaredOnly);
        var ro = methods.Where(m =>
            m.IsDefined(typeof(IsReadOnlyAttribute), false));
        Console.WriteLine("instance methods: " + methods.Length
            + ", readonly: " + ro.Count());
        Console.WriteLine("readonly: " + string.Join(" ",
            ro.Select(m => m.Name).Distinct().OrderBy(n => n,
                StringComparer.Ordinal)));
        Console.WriteLine("not readonly: " + string.Join(" ",
            methods.Except(ro).Select(m => m.Name)));
    }
}
