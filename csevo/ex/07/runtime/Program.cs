// 슬라이드 p7-v6-runtime — 같이 온 런타임, C# 6.0
using System;
using System.Linq;
using System.Runtime.CompilerServices;

class App
{
    static void Show(Type t)
    {
        string kind = t.IsInterface ? "interface"
            : t.IsAbstract && t.IsSealed ? "static class"
            : t.IsAbstract ? "abstract class" : "class";
        Console.WriteLine("{0,-25} {1,-14} {2}",
            t.Name, kind, t.Namespace);
        var names = t.GetMethods()
            .Where(m => m.DeclaringType == t && !m.IsSpecialName)
            .Select(m => m.Name).Distinct().OrderBy(n => n);
        Console.WriteLine("    " + string.Join(" ", names));
    }

    static void Main()
    {
        Show(typeof(IFormattable));
        Show(typeof(FormattableString));
        Show(typeof(FormattableStringFactory));
        Console.WriteLine();
        // the concrete type behind an interpolated FormattableString
        FormattableString f = $"{1}{2}";
        Type c = f.GetType();
        Console.WriteLine("{0} public={1}", c.FullName, c.IsPublic);
        Console.WriteLine(c.Assembly.GetName().Name);
    }
}
